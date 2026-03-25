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
            import logging

            logging.getLogger(__name__).warning(
                "No embedding model detected at %s. "
                "Falling back to local HuggingFace sentence-transformers. "
                "To silence this warning set "
                "THREAT_RAG_EMBEDDING_BACKEND=sentence-transformers.",
                vllm_base_url,
            )
        # vllm (no embedding model found) or auto: fall through
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

# SQLite (used by Chroma's embedded DB) caps the number of bound variables per
# query.  Older SQLite builds default to 999; newer ones allow up to 32 766.
# Stay well under the lower bound so we never hit the limit regardless of the
# installed version.
_CHROMA_GET_BATCH = 500


def _add_new_texts_batched(
    store,
    texts: list[str],
    metadatas: list[dict],
    ids: list[str],
    log=None,
) -> int:
    """
    Add only documents whose IDs are not already present in *store*.

    Existence checks are performed in batches of _CHROMA_GET_BATCH to avoid
    SQLite's "too many SQL variables" error when the collection is large.

    Returns the number of newly added documents.
    """
    existing: set[str] = set()
    for i in range(0, len(ids), _CHROMA_GET_BATCH):
        batch = ids[i : i + _CHROMA_GET_BATCH]
        result = store._collection.get(ids=batch, include=[])
        existing.update(result["ids"])

    new_texts: list[str] = []
    new_metas: list[dict] = []
    new_ids: list[str] = []
    for text, meta, doc_id in zip(texts, metadatas, ids):
        if doc_id not in existing:
            new_texts.append(text)
            new_metas.append(meta)
            new_ids.append(doc_id)

    skipped = len(ids) - len(new_ids)
    if skipped and log:
        log(f"  Skipping {skipped:,} already-indexed chunks.")

    if new_texts:
        store.add_texts(texts=new_texts, metadatas=new_metas, ids=new_ids)

    return len(new_ids)


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

    added_mitre = _add_new_texts_batched(
        mitre_store, mitre_texts, mitre_metas, mitre_ids, log=log
    )
    skipped_mitre = len(mitre_texts) - added_mitre
    log(
        f"Upserted {added_mitre:,} new MITRE chunks into 'mitre_techniques' collection"
        + (f" ({skipped_mitre:,} already present, skipped)." if skipped_mitre else ".")
    )

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

    added_cve = _add_new_texts_batched(
        cve_store, cve_texts, cve_metas, cve_ids, log=log
    )
    skipped_cve = len(cve_texts) - added_cve
    log(
        f"Upserted {added_cve:,} new CVE chunks into 'nvd_cves' collection"
        + (f" ({skipped_cve:,} already present, skipped)." if skipped_cve else ".")
    )


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
