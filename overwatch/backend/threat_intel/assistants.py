"""
CVE & ATT&CK AI Assistant wired to a local vLLM endpoint.

Uses two retrieval sources:
  1. Chroma vector store (MITRE ATT&CK techniques + NVD CVEs) — retrieval is
     performed manually in run_chat_task (tasks.py) before calling assistant.run()
     and prepended as a [THREAT INTEL CONTEXT] block in the user message.
     django-ai-assistant does not substitute {context} in instructions, so the
     old get_retriever() hook was a no-op.
  2. Live Django ORM queries via the query_django_db @method_tool
"""

from __future__ import annotations

import logging
import os
from typing import Optional

from django_ai_assistant import AIAssistant, method_tool

from threat_intel.rag import is_sensitive_field

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
        "You are a cybersecurity assistant specialising in MITRE ATT&CK techniques "
        "and NVD CVE records. "
        "To gather threat intelligence, explicitly call the search_cves and "
        "search_mitre_techniques tools. Use these to answer accurately and cite "
        "specific IDs (e.g. T1059, CVE-2021-44228). If you do not have enough "
        "information, say so explicitly rather than guessing. "
        "For questions about the organisation's own red-team logs and operations, "
        "use the query_django_db and get_related_records tools.\n"
        "Examples:\n"
        "- \"Find all evidence files uploaded during Operation Red October.\": Query "
        "operations for the ID, then query evidence files with that operation_id.\n"
        "- \"Show me the logs associated with the 'privilege-escalation' tag.\": "
        "Query logs with tag_name='privilege-escalation'.\n"
        "- \"What context do we have for Log ID 42?\": Use get_related_records('log', 42) "
        "to find associated files, tags, and relations.\n"
        "- \"Compare the tools used in Operation A vs Operation B.\": Retrieve logs/tags "
        "for both operations and compare them."
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

    # -------------------------------------------------------------------------
    # Threat Intel Tools
    # -------------------------------------------------------------------------

    @method_tool
    def search_cves(
        self, query: str, min_cvss: float = 0.0, limit: int = 5
    ) -> str:
        """
        Search the NVD CVE database using semantic similarity.

        Args:
            query: The threat, product, or vulnerability to search for.
            min_cvss: Minimum CVSS score to filter by (default 0.0).
            limit: Maximum number of CVEs to return.
        """
        from threat_intel.rag import get_cve_collection

        try:
            collection = get_cve_collection()
            filter_kwargs = {"cvss_score": {"$gte": min_cvss}} if min_cvss > 0.0 else None

            if not query.strip():
                # If query is empty, do a pure metadata search to avoid embedding errors
                res = collection._collection.get(where=filter_kwargs, limit=limit)
                documents = res.get("documents", [])
                if not documents:
                    return f"No CVEs found with CVSS >= {min_cvss}."
                return "\n\n".join(documents)

            results = collection.similarity_search(query, k=limit, filter=filter_kwargs)
            if not results:
                return f"No CVEs found matching '{query}' with CVSS >= {min_cvss}."
            return "\n\n".join(d.page_content for d in results)
        except Exception as e:
            logger.exception("Error searching CVEs")
            return f"Error searching CVEs: {e}"

    @method_tool
    def search_mitre_techniques(
        self, query: str, limit: int = 5
    ) -> str:
        """
        Search the MITRE ATT&CK database using semantic similarity.

        Args:
            query: The tactic, technique, or behavior to search for.
            limit: Maximum number of techniques to return.
        """
        from threat_intel.rag import get_mitre_collection

        try:
            collection = get_mitre_collection()
            results = collection.similarity_search(query, k=limit)
            if not results:
                return f"No MITRE techniques found matching '{query}'."
            return "\n\n".join(d.page_content for d in results)
        except Exception as e:
            logger.exception("Error searching MITRE techniques")
            return f"Error searching MITRE techniques: {e}"

    # -------------------------------------------------------------------------
    # Django DB tool
    # -------------------------------------------------------------------------

    @method_tool
    def query_django_db(
        self,
        query: str,
        model_name: Optional[str] = None,
        operation_id: Optional[int] = None,
        tag_name: Optional[str] = None,
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
            operation_id: Optional[int] = None. To filter logs, evidence files, or
                relations to a specific red-team operation ID.
            tag_name: Optional[str] = None. To filter logs or other models by a specific
                tag (e.g., "lateral-movement").
            limit: Maximum number of records to return (default 10, max 50).

        Returns:
            Formatted string of matching records (sensitive fields stripped),
            ordered by most-recent first, or a helpful error message.

        Tips:
            - For "recent activity" queries, use query="" to get the latest records.
            - To search across operations, set model_name="operation".
            - Use operation_id or tag_name to filter the query efficiently.
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
        q_filter = Q()
        if query:
            # Keyword search across all eligible text fields
            search_q = Q()
            for field in text_fields:
                search_q |= Q(**{f"{field}__icontains": query})
            q_filter &= search_q

        if tag_name:
            if target == "log":
                q_filter &= Q(tags__name__iexact=tag_name)
            elif target == "evidencefile":
                q_filter &= Q(log__tags__name__iexact=tag_name)
            elif target == "operation":
                q_filter &= Q(tag__name__iexact=tag_name)
            elif target == "tag":
                q_filter &= Q(name__iexact=tag_name)

        if operation_id:
            try:
                op_model = apps.get_model("operations", "Operation")
                op = op_model.objects.get(pk=operation_id)
                if target == "log":
                    q_filter &= Q(tags=op.tag_id)
                elif target == "evidencefile":
                    q_filter &= Q(log__tags=op.tag_id)
                elif target == "tag":
                    q_filter &= Q(id=op.tag_id)
                elif target == "operation":
                    q_filter &= Q(id=operation_id)
            except Exception:
                pass

        qs = model_class.objects.filter(q_filter).distinct().order_by(order_by)[:limit]

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

    @method_tool
    def get_related_records(self, model_name: str, record_id: int) -> str:
        """
        Get all related records for a specific object, allowing you to "pivot" through
        the dataset (e.g. from a Log to its Tags and Evidence Files).

        Args:
            model_name: The source model type (e.g. 'log', 'tag', 'operation', 'evidencefile').
            record_id: The ID (pk) of the source record.

        Returns:
            A formatted string listing the related tags, evidence files, and operations.
        """
        from django.apps import apps

        target = model_name.strip().lower()
        if target not in _SEARCHABLE_MODELS:
            return f"Unknown model '{model_name}'."

        app_label = _SEARCHABLE_MODELS[target]
        try:
            model_class = apps.get_model(app_label, target.title().replace("id", "ID"))
            obj = model_class.objects.get(pk=record_id)
        except Exception as e:
            return f"Error retrieving {target.title()} {record_id}: {e}"

        lines = []
        if target == "log":
            # pivot to tags and evidence
            tags = obj.tags.all()
            if tags:
                lines.append("Tags:")
                for t in tags:
                    lines.append(f"  - Tag(pk={t.pk}): name={t.name!r}")
            evidence = obj.evidence_files.all()
            if evidence:
                lines.append("Evidence Files:")
                for e in evidence:
                    lines.append(f"  - EvidenceFile(pk={e.pk}): original_filename={e.original_filename!r}")
            operations = apps.get_model("operations", "Operation").objects.filter(tag__in=tags)
            if operations:
                lines.append("Operations:")
                for o in operations:
                    lines.append(f"  - Operation(pk={o.pk}): name={o.name!r}")

        elif target == "tag":
            # pivot to logs and operations
            logs = obj.logs.order_by("-pk")[:10]
            if logs:
                lines.append("Recent Logs:")
                for l in logs:
                    lines.append(f"  - Log(pk={l.pk})")
            operations = obj.operations.all()
            if operations:
                lines.append("Operations:")
                for o in operations:
                    lines.append(f"  - Operation(pk={o.pk}): name={o.name!r}")

        elif target == "operation":
            # pivot to tag, then to logs
            if obj.tag:
                lines.append(f"Tag: Tag(pk={obj.tag.pk}) name={obj.tag.name!r}")
                logs = obj.tag.logs.order_by("-pk")[:10]
                if logs:
                    lines.append("Recent Logs:")
                    for l in logs:
                        lines.append(f"  - Log(pk={l.pk})")
            else:
                lines.append("No tag associated with this operation.")

        elif target == "evidencefile":
            # pivot to log
            if hasattr(obj, "log"):
                lines.append(f"Log: Log(pk={obj.log.pk})")

        if not lines:
            return f"No related records found for {target.title()} {record_id}."

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
