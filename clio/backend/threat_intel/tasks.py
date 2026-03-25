"""
Celery tasks for the threat_intel app.

The chat pipeline runs asynchronously so the HTTP response returns immediately
with a task_id.  The frontend polls GET /api/chat/tasks/{task_id}/ every 800ms
until the task completes (status = "complete" | "error").

Results are stored in Django's cache (Redis in production) with a 10-minute TTL.
"""

from __future__ import annotations

import logging

from celery import shared_task
from django.core.cache import cache
from django.utils.timezone import now

logger = logging.getLogger(__name__)

_CACHE_TTL = 600  # seconds — 10 minutes


@shared_task(bind=True)
def run_chat_task(
    self,
    message: str,
    thread_id_str: str,
    session_id: int | None = None,
) -> None:
    """
    Run the CveAttackAssistant synchronously inside a Celery worker and cache
    the result under the Celery task ID.

    Args:
        message:       The user's message text.
        thread_id_str: String representation of the django-ai-assistant Thread UUID.
        session_id:    Optional ChatSession PK.  When supplied the session's
                       updated_at timestamp is refreshed after a successful reply
                       so the sidebar ordering stays current.
    """
    task_id = self.request.id
    cache.set(f"chat_task:{task_id}", {"status": "running"}, timeout=_CACHE_TTL)

    try:
        from django_ai_assistant.models import Thread

        from threat_intel.assistants import CveAttackAssistant

        assistant = CveAttackAssistant()

        if thread_id_str:
            try:
                thread = Thread.objects.get(id=thread_id_str)
            except Thread.DoesNotExist:
                thread = Thread.objects.create(
                    created_by=None, assistant_id=assistant.id
                )
                logger.warning(
                    "Thread %s not found in task; created replacement %s",
                    thread_id_str,
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
                "thread_id": str(thread.id),
            },
            timeout=_CACHE_TTL,
        )

        # Bump session.updated_at so the sidebar ordering reflects recent usage.
        if session_id:
            from threat_intel.models import ChatSession

            ChatSession.objects.filter(id=session_id).update(updated_at=now())

        logger.info("Chat task %s complete  reply_len=%d", task_id, len(reply_text))

    except Exception as exc:
        logger.exception("Chat task %s failed", task_id)
        cache.set(
            f"chat_task:{task_id}",
            {"status": "error", "error": str(exc)},
            timeout=_CACHE_TTL,
        )
        raise
