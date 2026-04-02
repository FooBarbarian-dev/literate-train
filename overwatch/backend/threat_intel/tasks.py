"""
Celery tasks for the threat_intel app.

The chat pipeline runs asynchronously so the HTTP response returns immediately
with a task_id.  The frontend polls GET /api/chat/tasks/{task_id}/ every 800ms
until the task completes (status = "complete" | "error").

Results are stored in Django's cache (Redis in production) with a 10-minute TTL.
"""

from __future__ import annotations

import logging
import re

from celery import shared_task
from django.core.cache import cache
from django.utils.timezone import now

logger = logging.getLogger(__name__)

_CACHE_TTL = 600  # seconds — 10 minutes

# BUG 2/3: regexes to extract cited source IDs from assistant replies.
_CVE_RE = re.compile(r'CVE-\d{4}-\d{4,}')
_MITRE_RE = re.compile(r'T\d{4}(?:\.\d{3})?')


def _store_session_sources(session_id: int, reply_text: str) -> None:
    """
    Parse reply_text for CVE IDs and ATT&CK technique IDs and persist them
    as SessionSource records (BUG 2 + BUG 3).

    Uses get_or_create so repeated citations across turns don't cause duplicates.
    source_url is populated for MITRE and NVD records per BUG 3.
    """
    from threat_intel.models import SessionSource

    try:
        from threat_intel.models import ChatSession
        session = ChatSession.objects.get(id=session_id)
    except Exception:
        return

    cve_ids = set(_CVE_RE.findall(reply_text))
    mitre_ids = set(_MITRE_RE.findall(reply_text))

    for cve_id in cve_ids:
        try:
            SessionSource.objects.get_or_create(
                session=session,
                source_type=SessionSource.SOURCE_NVD,
                record_id=cve_id,
                defaults={
                    "source_url": f"https://nvd.nist.gov/vuln/detail/{cve_id}",
                },
            )
        except Exception as exc:
            logger.debug("Could not store NVD source %s: %s", cve_id, exc)

    for mitre_id in mitre_ids:
        # Convert T1059.001 → T1059/001 for the MITRE URL path.
        url_path = mitre_id.replace(".", "/")
        try:
            SessionSource.objects.get_or_create(
                session=session,
                source_type=SessionSource.SOURCE_MITRE,
                record_id=mitre_id,
                defaults={
                    "source_url": f"https://attack.mitre.org/techniques/{url_path}/",
                },
            )
        except Exception as exc:
            logger.debug("Could not store MITRE source %s: %s", mitre_id, exc)

    logger.debug(
        "Session %s sources stored: %d NVD, %d MITRE",
        session_id, len(cve_ids), len(mitre_ids),
    )


@shared_task(bind=True)
def run_chat_task(
    self,
    message: str,
    thread_id: int | None,
    session_id: int | None = None,
) -> None:
    """
    Run the CveAttackAssistant synchronously inside a Celery worker and cache
    the result under the Celery task ID.

    Args:
        message:    The user's message text.
        thread_id:  Integer PK of the django-ai-assistant Thread (BUG 1 fix —
                    was previously a UUID string; Thread.id is BigAutoField).
        session_id: Optional ChatSession PK.  When supplied:
                    - session.updated_at is refreshed after a successful reply
                    - SessionSource records are persisted for cited CVEs/techniques
                      (BUG 2 + BUG 3).
    """
    task_id = self.request.id
    cache.set(f"chat_task:{task_id}", {"status": "running"}, timeout=_CACHE_TTL)

    try:
        from django_ai_assistant.models import Thread

        from threat_intel.assistants import CveAttackAssistant

        assistant = CveAttackAssistant()

        if thread_id is not None:
            try:
                thread = Thread.objects.get(id=int(thread_id))
            except Thread.DoesNotExist:
                thread = Thread.objects.create(
                    created_by=None, assistant_id=assistant.id
                )
                logger.warning(
                    "Thread %s not found in task; created replacement %s",
                    thread_id,
                    thread.id,
                )
        else:
            thread = Thread.objects.create(
                created_by=None, assistant_id=assistant.id
            )

        logger.info(
            "Chat task %s  thread=%s  message=%r",
            task_id,
            thread.id,
            message[:120],
        )

        reply_text = assistant.run(message, thread_id=thread.id)
        if not isinstance(reply_text, str):
            reply_text = str(reply_text)

        cache.set(
            f"chat_task:{task_id}",
            {
                "status": "complete",
                "reply": reply_text,
                "thread_id": thread.id,
            },
            timeout=_CACHE_TTL,
        )

        if session_id:
            from threat_intel.models import ChatSession

            # Bump updated_at so the sidebar ordering reflects recent usage.
            ChatSession.objects.filter(id=session_id).update(updated_at=now())

            # BUG 2 + BUG 3: persist source citations extracted from the reply.
            _store_session_sources(session_id, reply_text)

        logger.info("Chat task %s complete  reply_len=%d", task_id, len(reply_text))

    except Exception as exc:
        logger.exception("Chat task %s failed", task_id)
        cache.set(
            f"chat_task:{task_id}",
            {"status": "error", "error": str(exc)},
            timeout=_CACHE_TTL,
        )
        raise
