"""
Chat API view for the threat_intel app.

  POST /api/chat/  — JSON endpoint consumed by the React Threat Intel page

Thread IDs are UUIDs; pass null / omit to start a new conversation.
"""

from __future__ import annotations

import logging
import uuid

from django.db.models import Q
from rest_framework import filters as drf_filters
from rest_framework import generics, serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from threat_intel.models import MitreTechnique, NvdCve

logger = logging.getLogger(__name__)


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
        except ConnectionError as exc:
            logger.exception("Chat assistant connection error")
            return Response(
                {"error": f"Unable to reach the AI model server: {exc}"},
                status=503,
            )
        except Exception as exc:
            logger.exception("Chat assistant error")
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
    from django_ai_assistant.models import Thread

    from threat_intel.assistants import CveAttackAssistant

    assistant = CveAttackAssistant()

    # Resolve user: Thread.created_by is a FK to AUTH_USER_MODEL, so we can
    # only pass a real Django User instance.  JWTUser (a dataclass used by
    # the stateless JWT auth backend) is *not* a model and will cause
    # ``ValueError`` if assigned.  Pass None in that case.
    from django.contrib.auth import get_user_model

    User = get_user_model()
    raw_user = getattr(request, "user", None)
    db_user = raw_user if isinstance(raw_user, User) else None

    # Retrieve or create the conversation thread
    thread: Thread | None
    if thread_id:
        try:
            thread = Thread.objects.get(id=thread_id)
        except Thread.DoesNotExist:
            thread = Thread.objects.create(
                created_by=db_user, assistant_id=assistant.id
            )
            thread_id = str(thread.id)
    else:
        thread = Thread.objects.create(
            created_by=db_user, assistant_id=assistant.id
        )
        thread_id = str(thread.id)

    # Send the user message and retrieve the AI reply (django-ai-assistant 0.4.x API)
    reply_text = assistant.run(message, thread_id=thread.id)

    if not isinstance(reply_text, str):
        reply_text = str(reply_text)

    return reply_text, thread_id


# ---------------------------------------------------------------------------
# MITRE ATT&CK  (GET /api/threat-intel/mitre/)
# ---------------------------------------------------------------------------


class MitreTechniqueSerializer(serializers.ModelSerializer):
    class Meta:
        model = MitreTechnique
        fields = [
            "id",
            "external_id",
            "name",
            "description",
            "domain",
            "tactics",
            "platforms",
            "ingested_at",
        ]


class MitreTechniqueListView(generics.ListAPIView):
    """
    GET /api/threat-intel/mitre/

    Query params:
        search    – free-text search on name, external_id, description
        domain    – filter by ATT&CK domain (enterprise-attack | mobile-attack | ics-attack)
        tactic    – filter by tactic phrase (substring match)
        ordering  – DRF ordering: external_id | name | domain | tactics (prefix - for desc)
    """

    permission_classes = [IsAuthenticated]
    serializer_class = MitreTechniqueSerializer
    filter_backends = [drf_filters.OrderingFilter]
    ordering_fields = ["external_id", "name", "domain", "tactics"]
    ordering = ["external_id"]

    def get_queryset(self):
        qs = MitreTechnique.objects.all()
        search = self.request.query_params.get("search", "").strip()
        domain = self.request.query_params.get("domain", "").strip()
        tactic = self.request.query_params.get("tactic", "").strip()
        if search:
            qs = qs.filter(
                Q(name__icontains=search)
                | Q(external_id__icontains=search)
                | Q(description__icontains=search)
            )
        if domain:
            qs = qs.filter(domain=domain)
        if tactic:
            qs = qs.filter(tactics__icontains=tactic)
        return qs


# ---------------------------------------------------------------------------
# NVD CVEs  (GET /api/threat-intel/cves/)
# ---------------------------------------------------------------------------


class NvdCveSerializer(serializers.ModelSerializer):
    class Meta:
        model = NvdCve
        fields = [
            "id",
            "cve_id",
            "description",
            "cvss_score",
            "published_date",
            "affected_products",
            "ingested_at",
        ]


class NvdCveListView(generics.ListAPIView):
    """
    GET /api/threat-intel/cves/

    Query params:
        search      – free-text search on cve_id, description, affected_products
        min_cvss    – minimum CVSS score (float)
        max_cvss    – maximum CVSS score (float)
        ordering    – DRF ordering: cve_id | cvss_score | published_date (prefix - for desc)
    """

    permission_classes = [IsAuthenticated]
    serializer_class = NvdCveSerializer
    filter_backends = [drf_filters.OrderingFilter]
    ordering_fields = ["cve_id", "cvss_score", "published_date"]
    ordering = ["-published_date"]

    def get_queryset(self):
        qs = NvdCve.objects.all()
        search = self.request.query_params.get("search", "").strip()
        min_cvss = self.request.query_params.get("min_cvss", "").strip()
        max_cvss = self.request.query_params.get("max_cvss", "").strip()
        if search:
            qs = qs.filter(
                Q(cve_id__icontains=search)
                | Q(description__icontains=search)
                | Q(affected_products__icontains=search)
            )
        if min_cvss:
            try:
                qs = qs.filter(cvss_score__gte=float(min_cvss))
            except ValueError:
                pass
        if max_cvss:
            try:
                qs = qs.filter(cvss_score__lte=float(max_cvss))
            except ValueError:
                pass
        return qs
