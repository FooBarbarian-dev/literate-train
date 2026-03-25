"""
CVE & ATT&CK AI Assistant wired to a local vLLM endpoint.

Uses two retrieval sources:
  1. Chroma vector store (MITRE ATT&CK techniques + NVD CVEs) via get_retriever()
  2. Live Django ORM queries via the query_django_db @method_tool
"""

from __future__ import annotations

import logging
import os
from typing import Optional

from django_ai_assistant import AIAssistant, method_tool

from threat_intel.rag import get_retriever as _rag_get_retriever, is_sensitive_field

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Models available for DB tool queries (app_label → model_name mapping).
# Derived from Phase 0 discovery; excludes models with no text search value.
# ---------------------------------------------------------------------------
_SEARCHABLE_MODELS: dict[str, str] = {
    "log": "logs",
    "tag": "tags",
    "operation": "operations",
    "evidencefile": "evidence",
    "logtemplate": "templates_mgmt",
    "relation": "relations",
    "filestatus": "relations",
    "logrelationship": "relations",
    "tagrelationship": "relations",
}


class CveAttackAssistant(AIAssistant):
    id = "cve_attack_assistant"
    name = "CVE & ATT&CK Assistant"
    instructions = (
        "You are a cybersecurity assistant with access to MITRE ATT&CK techniques "
        "and NVD CVE records. Answer questions using the provided context. "
        "Always cite specific CVE IDs or ATT&CK technique IDs (e.g. T1059) when "
        "they are relevant. If the context does not contain enough information, "
        "say so explicitly rather than guessing.\n\n"
        "Context:\n{context}"
    )

    def get_llm(self):
        from langchain_openai import ChatOpenAI

        base_url = os.environ.get("VLLM_BASE_URL", "http://localhost:8000/v1")
        api_key = os.environ.get("VLLM_API_KEY", "not-needed")
        model = os.environ.get("VLLM_MODEL_NAME", "")

        if not model:
            # Attempt to auto-detect the loaded model from the vLLM server
            logger.debug("VLLM_MODEL_NAME not set, auto-detecting from %s", base_url)
            model = _detect_vllm_chat_model(base_url) or ""

        if not model:
            raise RuntimeError(
                "No vLLM model name configured. Set the VLLM_MODEL_NAME "
                "environment variable to the model served by your vLLM instance "
                f"(VLLM_BASE_URL={base_url})."
            )

        logger.info("LLM request  model=%s  base_url=%s", model, base_url)

        return ChatOpenAI(
            base_url=base_url,
            api_key=api_key,
            model=model,
            temperature=0.1,
            request_timeout=120,
        )

    def get_retriever(self):
        """
        Return a MergerRetriever combining the MITRE ATT&CK and NVD CVE
        Chroma collections.  Falls back gracefully if the vector store has
        not been built yet.
        """
        try:
            retriever = _rag_get_retriever()
            logger.info(
                "RAG retriever ready  collections=[mitre_techniques, nvd_cves]  k=3 each"
            )
            return retriever
        except Exception as exc:
            # If Chroma collections are empty (no ingestion yet), return a
            # no-op retriever rather than crashing.
            logger.warning(
                "RAG retriever unavailable: %s. "
                "Run `manage.py ingest_threat_data` to build the index.",
                exc,
            )
            from langchain_core.retrievers import BaseRetriever
            from langchain_core.documents import Document

            class _EmptyRetriever(BaseRetriever):
                def _get_relevant_documents(self, query, *, run_manager=None):
                    return []

            return _EmptyRetriever()

    # -------------------------------------------------------------------------
    # Django DB tool
    # -------------------------------------------------------------------------

    @method_tool
    def query_django_db(
        self,
        query: str,
        model_name: Optional[str] = None,
        limit: int = 10,
    ) -> str:
        """
        Search the application's live Django database for records matching
        the given query string.

        Args:
            query: Keyword to search for (e.g. "powershell", "CVE-2021").
                   Pass an empty string "" to retrieve the most recent records
                   without filtering — useful for "show me recent activity"
                   style questions.
            model_name: Model to search. One of: Log, Tag, Operation,
                EvidenceFile, LogTemplate, Relation, FileStatus, LogRelationship,
                TagRelationship.  Defaults to Log if omitted.
            limit: Maximum number of records to return (default 10, max 50).

        Returns:
            Formatted string of matching records (sensitive fields stripped),
            ordered by most-recent first, or a helpful error message.

        Tips:
            - For "recent activity" queries, use query="" to get the latest records.
            - To search across operations, set model_name="operation".
            - CVE and ATT&CK technique data comes from the RAG vector store, not
              this tool — only use this tool for red-team log/operation data.
        """
        from django.apps import apps
        from django.db.models import Q

        target = (model_name or "log").strip().lower()
        limit = max(1, min(limit, 50))

        logger.info("DB tool query  model=%s  query=%r  limit=%d", target, query[:120], limit)

        if target not in _SEARCHABLE_MODELS:
            available = ", ".join(
                m.title() for m in sorted(_SEARCHABLE_MODELS.keys())
            )
            return (
                f"Unknown model '{model_name}'. "
                f"Available models: {available}"
            )

        app_label = _SEARCHABLE_MODELS[target]
        model_class = apps.get_model(app_label, target.title().replace("id", "ID"))

        _TEXT_TYPES = frozenset({"CharField", "TextField", "GenericIPAddressField"})
        text_fields = [
            f.name
            for f in model_class._meta.get_fields()
            if (
                hasattr(f, "get_internal_type")
                and f.get_internal_type() in _TEXT_TYPES
                and not is_sensitive_field(f.name)
            )
        ]

        # Determine ordering: prefer created_at DESC, fall back to -pk
        field_names = {f.name for f in model_class._meta.get_fields() if hasattr(f, "name")}
        order_by = "-created_at" if "created_at" in field_names else "-pk"

        query = (query or "").strip()
        if query:
            # Keyword search across all eligible text fields
            q_filter = Q()
            for field in text_fields:
                q_filter |= Q(**{f"{field}__icontains": query})
            qs = model_class.objects.filter(q_filter).order_by(order_by)[:limit]
        else:
            # No query — return most recent records
            qs = model_class.objects.all().order_by(order_by)[:limit]

        result_count = len(qs)
        logger.info(
            "DB tool result  model=%s  query=%r  hits=%d",
            target,
            query[:80],
            result_count,
        )

        if not qs:
            if query:
                return f"No {target.title()} records found matching '{query}'."
            return f"No {target.title()} records found in the database."

        # Build display fields: all non-sensitive text + numeric fields
        _DISPLAY_TYPES = _TEXT_TYPES | frozenset({"IntegerField", "BigIntegerField",
                                                   "FloatField", "DateTimeField", "DateField"})
        lines: list[str] = []
        for obj in qs:
            parts: list[str] = []
            for f in model_class._meta.get_fields():
                if not hasattr(f, "get_internal_type"):
                    continue
                if is_sensitive_field(f.name):
                    continue
                if f.get_internal_type() in _DISPLAY_TYPES:
                    value = getattr(obj, f.name, None)
                    if value is not None and value != "":
                        parts.append(f"{f.name}={str(value)[:120]!r}")
            lines.append(f"{target.title()}(pk={obj.pk}): {', '.join(parts)}")

        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _detect_vllm_chat_model(base_url: str) -> str | None:
    """Return the first non-embedding model id from the vLLM /v1/models list."""
    try:
        import httpx

        resp = httpx.get(f"{base_url.rstrip('/')}/models", timeout=5)
        resp.raise_for_status()
        for model in resp.json().get("data", []):
            model_id: str = model.get("id", "")
            model_type: str = model.get("model_type", "")
            if model_type != "embedding" and "embed" not in model_id.lower():
                logger.debug("Auto-detected vLLM chat model: %s", model_id)
                return model_id
    except Exception as exc:
        logger.debug("vLLM model auto-detection failed: %s", exc)
    return None
