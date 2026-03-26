import json
import logging
from celery import shared_task
from django.db import transaction
from logs.models import Log, LogAIContext, LogAIContextSource
from threat_intel.rag import _chroma_collection, get_embeddings
from threat_intel.assistants import CveAttackAssistant

logger = logging.getLogger(__name__)

@shared_task
def generate_log_ai_context(log_entry_id: int, context_id: int, user_id: int):
    """
    Query Chroma for MITRE and NVD records relevant to the log entry,
    call the LLM to produce structured analysis, persist results.
    """
    try:
        log_entry = Log.objects.get(id=log_entry_id)
        context = LogAIContext.objects.get(id=context_id)
    except (Log.DoesNotExist, LogAIContext.DoesNotExist):
        logger.error(f"generate_log_ai_context: log_entry_id={log_entry_id} or context_id={context_id} not found.")
        return

    try:
        # Build query string
        # command text + hostname + username + tags
        tags_names = [tag.name for tag in log_entry.tags.all()]
        query_parts = []
        if log_entry.command:
            query_parts.append(log_entry.command)
        if log_entry.hostname:
            query_parts.append(log_entry.hostname)
        if log_entry.username:
            query_parts.append(log_entry.username)
        if tags_names:
            query_parts.append(" ".join(tags_names))

        query_str = " ".join(query_parts)
        if not query_str.strip():
            query_str = "unknown activity"

        embeddings = get_embeddings()

        # Query MITRE
        mitre_store = _chroma_collection("mitre_techniques", embeddings)
        mitre_docs = mitre_store.similarity_search(query_str, k=5)

        mitre_context_lines = []
        retrieved_mitre = []
        for doc in mitre_docs:
            meta = doc.metadata
            tech_id = meta.get("external_id")
            if not tech_id:
                continue
            retrieved_mitre.append({
                "source_type": "mitre",
                "record_id": tech_id,
                "source_url": f"https://attack.mitre.org/techniques/{tech_id.replace('.', '/')}/"
            })
            tactic = meta.get("tactic", "[]")
            try:
                tactic_list = json.loads(tactic)
                tactic_str = ", ".join(tactic_list) if isinstance(tactic_list, list) else tactic
            except:
                tactic_str = tactic

            mitre_context_lines.append(
                f"Technique ID: {tech_id}\n"
                f"Name: {meta.get('name', '')}\n"
                f"Tactic: {tactic_str}\n"
                f"Description: {doc.page_content}\n"
            )

        mitre_context_block = "\n".join(mitre_context_lines)

        # Query NVD
        cve_store = _chroma_collection("nvd_cves", embeddings)
        cve_docs = cve_store.similarity_search(query_str, k=5)

        cve_context_lines = []
        retrieved_nvd = []
        for doc in cve_docs:
            meta = doc.metadata
            cve_id = meta.get("cve_id")
            if not cve_id:
                continue
            retrieved_nvd.append({
                "source_type": "nvd",
                "record_id": cve_id,
                "source_url": f"https://nvd.nist.gov/vuln/detail/{cve_id}"
            })

            cve_context_lines.append(
                f"CVE ID: {cve_id}\n"
                f"CVSS Score: {meta.get('cvss_score', '')}\n"
                f"Published: {meta.get('published_date', '')}\n"
                f"Description: {doc.page_content}\n"
            )

        nvd_context_block = "\n".join(cve_context_lines)

        # Build prompt
        prompt = f"""You are a threat intelligence analyst. Analyze the following C2 beacon log entry
and the retrieved context from MITRE ATT&CK and NVD CVE databases.

LOG ENTRY:
Hostname: {log_entry.hostname}
Internal IP: {log_entry.internal_ip}
Username: {log_entry.username}
Command: {log_entry.command}
Notes: {log_entry.notes}
Tags: {", ".join(tags_names)}

RETRIEVED MITRE TECHNIQUES (top candidates):
{mitre_context_block}

RETRIEVED NVD CVES (top candidates):
{nvd_context_block}

Return ONLY valid JSON matching this schema — no preamble, no markdown fences:
{{
  "summary": "2-3 sentence analyst summary of what this log entry represents",
  "mitre_techniques": [
    {{
      "technique_id": "...",
      "name": "...",
      "tactic": "...",
      "description": "one sentence",
      "url": "https://attack.mitre.org/techniques/{{id}}/",
      "relevance_note": "one sentence explaining why this technique matches"
    }}
  ],
  "cves": [
    {{
      "cve_id": "...",
      "cvss_score": 0.0,
      "description": "one sentence",
      "url": "https://nvd.nist.gov/vuln/detail/{{id}}",
      "relevance_note": "one sentence explaining why this CVE is relevant"
    }}
  ]
}}
Include only techniques/CVEs that are genuinely relevant. Omit irrelevant ones
even if retrieved. Return at most 3 techniques and 3 CVEs."""

        assistant = CveAttackAssistant()
        llm = assistant.get_llm()

        response = llm.invoke(prompt)
        content = response.content.strip()

        # Parse JSON
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]

        content = content.strip()
        result_data = json.loads(content)

        # Persist results
        with transaction.atomic():
            context.status = "complete"
            context.summary = result_data.get("summary", "")
            context.mitre_techniques = result_data.get("mitre_techniques", [])
            context.cves = result_data.get("cves", [])
            context.save()

            # Save sources (only those returned by LLM to be perfectly precise,
            # wait, spec says "one LogAIContextSource per Chroma record that was actually used in the LLM prompt (not just retrieved — only the ones passed to the prompt)."
            # Wait, the prompt says "Every time generate_log_ai_context completes, persist one LogAIContextSource per Chroma record that was actually used in the LLM prompt (not just retrieved — only the ones passed to the prompt)."
            # Actually, I pass all retrieved_mitre and retrieved_nvd to the prompt!
            # So I should persist all of them, or only the ones the LLM selected?
            # "used in the LLM prompt ... only the ones passed to the prompt"
            # Since I passed retrieved_mitre to the prompt, I persist them.

            # Using a set to avoid duplicates since chunks might have same ID
            seen_sources = set()
            for src in retrieved_mitre + retrieved_nvd:
                key = (src["source_type"], src["record_id"])
                if key not in seen_sources:
                    seen_sources.add(key)
                    LogAIContextSource.objects.create(
                        ai_context=context,
                        source_type=src["source_type"],
                        record_id=src["record_id"],
                        source_url=src["source_url"]
                    )

    except Exception as e:
        logger.exception("Error generating log AI context")
        context.status = "error"
        context.error_message = str(e)
        context.save()
        raise e
