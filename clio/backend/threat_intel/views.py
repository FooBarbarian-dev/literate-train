"""
Chat API view for the threat_intel app.

  POST /api/chat/  — JSON endpoint consumed by the React Threat Intel page

Thread IDs are UUIDs; pass null / omit to start a new conversation.
"""

from __future__ import annotations

import uuid

from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView


# ---------------------------------------------------------------------------
# JSON API endpoint  (POST /api/chat/)
# ---------------------------------------------------------------------------


class ChatAPIView(APIView):
    """
    POST /api/chat/

    Request body:
        {
            "message": "What CVEs affect Apache Log4j?",
            "thread_id": null          // omit or null to start a new thread
        }

    Response:
        {
            "reply": "...",
            "thread_id": "uuid-string"
        }

    Authentication: requires a valid session (JWT auth_token cookie).
    """

    permission_classes = [IsAuthenticated]

    def post(self, request: Request, *args, **kwargs) -> Response:
        message: str = (request.data.get("message") or "").strip()
        if not message:
            return Response(
                {"error": "'message' field is required and must not be empty."},
                status=400,
            )

        thread_id: str | None = request.data.get("thread_id") or None

        try:
            reply, thread_id = _run_assistant(message, thread_id, request)
        except RuntimeError as exc:
            # Surface vLLM/config errors clearly
            return Response({"error": str(exc)}, status=503)
        except Exception as exc:
            return Response({"error": f"Assistant error: {exc}"}, status=500)

        return Response({"reply": reply, "thread_id": thread_id})


# ---------------------------------------------------------------------------
# Assistant dispatch helper
# ---------------------------------------------------------------------------


def _run_assistant(
    message: str,
    thread_id: str | None,
    request,
) -> tuple[str, str]:
    """
    Create or resume a django-ai-assistant Thread, send a message, and
    return (reply_text, thread_id).
    """
    from django_ai_assistant.helpers.assistants import (
        create_message,
        create_thread,
    )
    from django_ai_assistant.models import Thread

    from threat_intel.assistants import CveAttackAssistant

    assistant = CveAttackAssistant()

    # Resolve user: use request.user if authenticated, else None (anonymous)
    user = getattr(request, "user", None)
    if user is not None and not user.is_authenticated:
        user = None

    # Retrieve or create the conversation thread
    thread: Thread
    if thread_id:
        try:
            thread = Thread.objects.get(id=thread_id)
        except Thread.DoesNotExist:
            thread = create_thread(assistant=assistant, created_by=user)
            thread_id = str(thread.id)
    else:
        thread = create_thread(assistant=assistant, created_by=user)
        thread_id = str(thread.id)

    # Send the user message and retrieve the AI reply
    output = create_message(
        assistant=assistant,
        thread=thread,
        user=user,
        content=message,
    )

    reply_text: str
    if hasattr(output, "content"):
        reply_text = str(output.content)
    elif isinstance(output, str):
        reply_text = output
    else:
        reply_text = str(output)

    return reply_text, thread_id
