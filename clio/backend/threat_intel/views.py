"""
Chat API view for the threat_intel app.

  POST /api/chat/  — JSON endpoint consumed by the React Threat Intel page

Thread IDs are UUIDs; pass null / omit to start a new conversation.
"""

from __future__ import annotations

import logging
import time
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


def _connection_error_types() -> tuple:
    """Return a tuple of exception classes that represent connection failures."""
    exc_types: list[type] = [ConnectionError]
    try:
        from openai import APIConnectionError

        exc_types.append(APIConnectionError)
    except ImportError:
        pass
    try:
        from httpx import ConnectError

        exc_types.append(ConnectError)
    except ImportError:
        pass
    return tuple(exc_types)


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

        user_label = getattr(request.user, "username", None) or str(
            getattr(request.user, "id", "anon")
        )
        logger.info(
            "Chat request  user=%s  thread=%s  message=%r",
            user_label,
            thread_id or "(new)",
            message[:120],
        )

        t0 = time.monotonic()
        try:
            reply, thread_id = _run_assistant(message, thread_id, request)
        except RuntimeError as exc:
            # Surface vLLM/config errors clearly
            logger.error("Chat config/runtime error: %s", exc)
            return Response({"error": str(exc)}, status=503)
        except (_connection_error_types()) as exc:
            logger.exception("Chat assistant connection error")
            return Response(
                {"error": f"Unable to reach the AI model server: {exc}"},
                status=503,
            )
        except Exception as exc:
            logger.exception("Chat assistant error")
            return Response({"error": f"Assistant error: {exc}"}, status=500)

        elapsed = time.monotonic() - t0
        logger.info(
            "Chat response  thread=%s  elapsed=%.1fs  reply_len=%d",
            thread_id,
            elapsed,
            len(reply),
        )

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
            logger.debug("Resumed existing thread %s", thread_id)
        except Thread.DoesNotExist:
            thread = Thread.objects.create(
                created_by=db_user, assistant_id=assistant.id
            )
            thread_id = str(thread.id)
            logger.debug("Thread %s not found, created new thread %s", thread_id, thread.id)
    else:
        thread = Thread.objects.create(
            created_by=db_user, assistant_id=assistant.id
        )
        thread_id = str(thread.id)
        logger.debug("Created new thread %s", thread_id)

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


class MitreFacetsView(APIView):
    """GET /api/threat-intel/mitre/facets/ — distinct domains and tactics for filter dropdowns."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        domains = sorted(
            MitreTechnique.objects.exclude(domain="")
            .values_list("domain", flat=True)
            .distinct()
        )
        tactic_rows = MitreTechnique.objects.exclude(tactics="").values_list("tactics", flat=True)
        tactic_set: set[str] = set()
        for row in tactic_rows:
            for t in row.split(","):
                t = t.strip()
                if t:
                    tactic_set.add(t)
        return Response({"domains": list(domains), "tactics": sorted(tactic_set)})


class MitreTechniqueListView(generics.ListAPIView):
    """
    GET /api/threat-intel/mitre/

    Query params:
        search    – free-text search on name, external_id, description
        domain    – repeat for multiple: ?domain=enterprise-attack&domain=ics-attack
        tactic    – repeat for multiple tactic substrings
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
        domains = [d for d in self.request.query_params.getlist("domain") if d.strip()]
        tactics = [t for t in self.request.query_params.getlist("tactic") if t.strip()]
        if search:
            qs = qs.filter(
                Q(name__icontains=search)
                | Q(external_id__icontains=search)
                | Q(description__icontains=search)
            )
        if domains:
            qs = qs.filter(domain__in=domains)
        if tactics:
            tq = Q()
            for t in tactics:
                tq |= Q(tactics__icontains=t)
            qs = qs.filter(tq)
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
        search           – free-text search on cve_id, description, affected_products
        cvss_severity    – repeat for multiple: none | low | medium | high | critical
        published_after  – ISO date string (inclusive)
        published_before – ISO date string (inclusive)
        ordering         – DRF ordering: cve_id | cvss_score | published_date (prefix - for desc)
    """

    permission_classes = [IsAuthenticated]
    serializer_class = NvdCveSerializer
    filter_backends = [drf_filters.OrderingFilter]
    ordering_fields = ["cve_id", "cvss_score", "published_date"]
    ordering = ["-published_date"]

    _SEVERITY_MAP = {
        "none":     Q(cvss_score__isnull=True),
        "low":      Q(cvss_score__isnull=False, cvss_score__lt=4.0),
        "medium":   Q(cvss_score__gte=4.0, cvss_score__lt=7.0),
        "high":     Q(cvss_score__gte=7.0, cvss_score__lt=9.0),
        "critical": Q(cvss_score__gte=9.0),
    }

    def get_queryset(self):
        qs = NvdCve.objects.all()
        search = self.request.query_params.get("search", "").strip()
        severities = [s for s in self.request.query_params.getlist("cvss_severity") if s in self._SEVERITY_MAP]
        published_after = self.request.query_params.get("published_after", "").strip()
        published_before = self.request.query_params.get("published_before", "").strip()

        if search:
            qs = qs.filter(
                Q(cve_id__icontains=search)
                | Q(description__icontains=search)
                | Q(affected_products__icontains=search)
            )
        if severities:
            sq = Q()
            for s in severities:
                sq |= self._SEVERITY_MAP[s]
            qs = qs.filter(sq)
        if published_after:
            qs = qs.filter(published_date__date__gte=published_after)
        if published_before:
            qs = qs.filter(published_date__date__lte=published_before)
        return qs
