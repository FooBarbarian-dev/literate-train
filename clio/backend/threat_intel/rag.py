"""
RAG pipeline helpers: embedding model selection, Chroma vector store
ingestion, and retriever construction.

The embedding model is chosen based on THREAT_RAG_EMBEDDING_BACKEND:
    "vllm"                - always use vLLM /v1/embeddings endpoint
    "sentence-transformers"- always use HuggingFace local model
    "auto" (default)      - probe vLLM; fall back to sentence-transformers
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any

from django.conf import settings

if TYPE_CHECKING:
    from langchain_core.embeddings import Embeddings
    from langchain_core.retrievers import BaseRetriever

# Fields whose names contain any of these substrings are stripped from DB
# tool output unconditionally.
SENSITIVE_SUBSTRINGS: frozenset[str] = frozenset(
    {"password", "token", "secret", "key", "hash"}
)


def is_sensitive_field(field_name: str) -> bool:
    name = field_name.lower()
    return any(sub in name for sub in SENSITIVE_SUBSTRINGS)


# ---------------------------------------------------------------------------
# Embedding model selection
# ---------------------------------------------------------------------------


def get_embeddings() -> "Embeddings":
    """Return the configured embedding model."""
    backend: str = getattr(settings, "THREAT_RAG_EMBEDDING_BACKEND", "auto")
    vllm_base_url: str = getattr(
        settings, "VLLM_BASE_URL", "http://localhost:8000/v1"
    )

    if backend == "sentence-transformers":
        return _huggingface_embeddings()

    if backend in ("vllm", "auto"):
        model_name = _detect_vllm_embedding_model(vllm_base_url)
        if model_name:
            from langchain_openai import OpenAIEmbeddings

            return OpenAIEmbeddings(
                base_url=vllm_base_url,
                api_key=getattr(settings, "VLLM_API_KEY", "not-needed"),
                model=model_name,
            )
        if backend == "vllm":
            raise RuntimeError(
                f"No embedding model detected at {vllm_base_url}. "
                "Check the VLLM_BASE_URL environment variable, or set "
                "THREAT_RAG_EMBEDDING_BACKEND=sentence-transformers to use "
                "a local HuggingFace model instead."
            )
        # auto: fall through to sentence-transformers
        return _huggingface_embeddings()

    raise ValueError(
        f"Unknown THREAT_RAG_EMBEDDING_BACKEND: {backend!r}. "
        "Valid choices: 'auto', 'vllm', 'sentence-transformers'."
    )


def _detect_vllm_embedding_model(base_url: str) -> str | None:
    """
    Call GET /v1/models and return the id of the first embedding model found,
    or None if none is available or the server is unreachable.
    """
    try:
        import httpx

        resp = httpx.get(f"{base_url.rstrip('/')}/models", timeout=5)
        resp.raise_for_status()
        for model in resp.json().get("data", []):
            model_id: str = model.get("id", "")
            model_type: str = model.get("model_type", "")
            # vLLM marks embedding models via model_type or the id containing "embed"
            if model_type == "embedding" or "embed" in model_id.lower():
                return model_id
    except Exception:
        pass
    return None


def _huggingface_embeddings() -> "Embeddings":
    from langchain_community.embeddings import HuggingFaceEmbeddings

    return HuggingFaceEmbeddings(model_name="BAAI/bge-small-en-v1.5")


# ---------------------------------------------------------------------------
# Chroma collection helper
# ---------------------------------------------------------------------------


def _chroma_db_path() -> Path:
    return Path(settings.BASE_DIR) / "threat_data" / "chroma_db"


def _chroma_collection(collection_name: str, embeddings: "Embeddings"):
    """Return a LangChain Chroma vector store backed by a persistent client."""
    import chromadb
    from langchain_community.vectorstores import Chroma

    db_path = _chroma_db_path()
    db_path.mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(path=str(db_path))
    return Chroma(
        client=client,
        collection_name=collection_name,
        embedding_function=embeddings,
    )


# ---------------------------------------------------------------------------
# Vector store ingestion
# ---------------------------------------------------------------------------


def build_vector_store(
    base: Path,
    techniques: list[dict],
    cves: list[dict],
    stdout: Any = None,
    stderr: Any = None,
) -> None:
    """
    Ingest normalized MITRE techniques and NVD CVEs into the Chroma vector
    store.  Uses the document `id` field as the Chroma document ID so
    repeated runs are idempotent (upsert semantics).
    """
    from langchain.text_splitter import RecursiveCharacterTextSplitter

    def log(msg: str) -> None:
        if stdout:
            stdout.write(msg)
        else:
            print(msg)

    def err(msg: str) -> None:
        if stderr:
            stderr.write(msg)
        else:
            print(f"ERROR: {msg}")

    embeddings = get_embeddings()
    splitter = RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=50)

    # ---- MITRE techniques ----
    log(f"Embedding {len(techniques)} MITRE techniques…")
    mitre_store = _chroma_collection("mitre_techniques", embeddings)

    mitre_texts: list[str] = []
    mitre_ids: list[str] = []
    mitre_metas: list[dict] = []

    for t in techniques:
        text = (
            f"ATT&CK Technique: {t.get('external_id', '')} — {t.get('name', '')}\n"
            f"Tactics: {', '.join(t.get('tactic', []))}\n"
            f"Platforms: {', '.join(t.get('platforms', []))}\n"
            f"Domain: {t.get('domain', '')}\n"
            f"Description: {t.get('description', '')}"
        )
        chunks = splitter.split_text(text)
        for i, chunk in enumerate(chunks):
            mitre_ids.append(f"{t['id']}_{i}")
            mitre_texts.append(chunk)
            mitre_metas.append(
                {
                    "external_id": t.get("external_id", ""),
                    "name": t.get("name", ""),
                    "tactic": json.dumps(t.get("tactic", [])),
                    "domain": t.get("domain", ""),
                }
            )

    if mitre_texts:
        mitre_store.add_texts(
            texts=mitre_texts, metadatas=mitre_metas, ids=mitre_ids
        )
    log(f"Upserted {len(mitre_texts)} MITRE chunks into 'mitre_techniques' collection.")

    # ---- NVD CVEs ----
    log(f"Embedding {len(cves)} NVD CVEs…")
    cve_store = _chroma_collection("nvd_cves", embeddings)

    cve_texts: list[str] = []
    cve_ids: list[str] = []
    cve_metas: list[dict] = []

    for c in cves:
        products_preview = ", ".join(c.get("affected_products", [])[:5])
        text = (
            f"CVE ID: {c.get('id', '')}\n"
            f"CVSS Score: {c.get('cvss_score', 'N/A')}\n"
            f"Published: {c.get('published_date', '')}\n"
            f"Affected Products: {products_preview}\n"
            f"Description: {c.get('description', '')}"
        )
        chunks = splitter.split_text(text)
        for i, chunk in enumerate(chunks):
            cve_ids.append(f"{c['id']}_{i}")
            cve_texts.append(chunk)
            cve_metas.append(
                {
                    "cve_id": c.get("id", ""),
                    "cvss_score": str(c.get("cvss_score", "")),
                    "published_date": c.get("published_date", ""),
                }
            )

    if cve_texts:
        cve_store.add_texts(texts=cve_texts, metadatas=cve_metas, ids=cve_ids)
    log(f"Upserted {len(cve_texts)} CVE chunks into 'nvd_cves' collection.")


# ---------------------------------------------------------------------------
# Retriever factory
# ---------------------------------------------------------------------------


def get_retriever() -> "BaseRetriever":
    """
    Return a merged LangChain retriever that queries both the
    'mitre_techniques' and 'nvd_cves' Chroma collections, returning
    the top 3 results from each (6 combined).
    """
    from langchain.retrievers import MergerRetriever

    embeddings = get_embeddings()
    mitre_store = _chroma_collection("mitre_techniques", embeddings)
    cve_store = _chroma_collection("nvd_cves", embeddings)

    return MergerRetriever(
        retrievers=[
            mitre_store.as_retriever(search_kwargs={"k": 3}),
            cve_store.as_retriever(search_kwargs={"k": 3}),
        ]
    )
