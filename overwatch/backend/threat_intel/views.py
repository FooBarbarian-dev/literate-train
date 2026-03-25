"""
Chat API view for the threat_intel app.

  POST /api/chat/                         — send a message (legacy: sync; session: async+poll)
  GET  /api/chat/sessions/                — list sessions for current user
  POST /api/chat/sessions/                — create session
  PATCH /api/chat/sessions/{id}/          — rename session
  DELETE /api/chat/sessions/{id}/         — delete session
  GET  /api/chat/sessions/{id}/messages/  — load message history
  GET  /api/chat/tasks/{task_id}/         — poll Celery task status
  GET  /api/chat/rag-status/              — RAG data-source panel
"""

from __future__ import annotations

import logging
import time
import uuid
from pathlib import Path

from django.conf import settings
from django.db.models import Count, Q
from django.utils.timezone import now
from rest_framework import filters as drf_filters
from rest_framework import generics, serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from threat_intel.models import ChatSession, MitreTechnique, NvdCve

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
# Assistant dispatch helper (used by legacy ChatAPIView path)
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


# ---------------------------------------------------------------------------
# Helper: get the username from a JWT or Django user
# ---------------------------------------------------------------------------


def _get_username(request) -> str:
    user = getattr(request, "user", None)
    if user is None:
        return ""
    return str(getattr(user, "username", None) or getattr(user, "id", ""))


# ---------------------------------------------------------------------------
# Session CRUD   (GET/POST /api/chat/sessions/,  PATCH/DELETE /api/chat/sessions/{id}/)
# ---------------------------------------------------------------------------


class ChatSessionListCreateView(APIView):
    """
    GET  /api/chat/sessions/  — list all sessions for the current user, newest first.
    POST /api/chat/sessions/  — create a new session; the django-ai-assistant Thread
                                is created immediately so a thread_id is available
                                when the first message is sent.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        username = _get_username(request)
        sessions = ChatSession.objects.filter(username=username).values(
            "id", "name", "thread_id", "created_at", "updated_at"
        )
        data = [
            {
                "id": s["id"],
                "name": s["name"],
                "thread_id": str(s["thread_id"]),
                "created_at": s["created_at"].isoformat(),
                "updated_at": s["updated_at"].isoformat(),
            }
            for s in sessions
        ]
        return Response(data)

    def post(self, request: Request) -> Response:
        username = _get_username(request)

        # Create the backing Thread immediately so thread_id is stable.
        try:
            from django_ai_assistant.models import Thread

            from threat_intel.assistants import CveAttackAssistant

            assistant = CveAttackAssistant()
            thread = Thread.objects.create(
                created_by=None, assistant_id=assistant.id
            )
            thread_id = thread.id
        except Exception as exc:
            logger.warning("Could not create Thread via django-ai-assistant: %s", exc)
            # Fall back to a bare UUID — the task will create the Thread on first send.
            thread_id = uuid.uuid4()

        session = ChatSession.objects.create(
            thread_id=thread_id,
            username=username,
            name="",
        )
        return Response(
            {
                "id": session.id,
                "name": session.name,
                "thread_id": str(session.thread_id),
                "created_at": session.created_at.isoformat(),
                "updated_at": session.updated_at.isoformat(),
            },
            status=201,
        )


class ChatSessionDetailView(APIView):
    """
    PATCH  /api/chat/sessions/{id}/  — rename session.  Body: {"name": "…"}
    DELETE /api/chat/sessions/{id}/  — delete session and its backing Thread + messages.
    """

    permission_classes = [IsAuthenticated]

    def _get_session(self, pk: int, username: str) -> ChatSession | None:
        try:
            return ChatSession.objects.get(id=pk, username=username)
        except ChatSession.DoesNotExist:
            return None

    def patch(self, request: Request, pk: int) -> Response:
        username = _get_username(request)
        session = self._get_session(pk, username)
        if session is None:
            return Response({"error": "Session not found."}, status=404)

        new_name = (request.data.get("name") or "").strip()
        if not new_name:
            return Response({"error": "'name' is required."}, status=400)

        session.name = new_name[:255]
        session.save(update_fields=["name", "updated_at"])
        return Response(
            {
                "id": session.id,
                "name": session.name,
                "thread_id": str(session.thread_id),
                "updated_at": session.updated_at.isoformat(),
            }
        )

    def delete(self, request: Request, pk: int) -> Response:
        username = _get_username(request)
        session = self._get_session(pk, username)
        if session is None:
            return Response({"error": "Session not found."}, status=404)

        thread_id = session.thread_id
        session.delete()

        # Best-effort deletion of the backing Thread and its messages.
        try:
            from django_ai_assistant.models import Thread

            Thread.objects.filter(id=thread_id).delete()
        except Exception as exc:
            logger.debug("Could not delete Thread %s: %s", thread_id, exc)

        return Response(status=204)


# ---------------------------------------------------------------------------
# Message history   GET /api/chat/sessions/{id}/messages/
# ---------------------------------------------------------------------------


class ChatSessionMessagesView(APIView):
    """
    GET /api/chat/sessions/{id}/messages/

    Returns the full conversation history for a session as a list of
    {role, content, created_at} objects, ordered oldest-first.

    Role values are normalised to "user" / "assistant" regardless of what
    django-ai-assistant stores internally ("human" / "ai").
    """

    permission_classes = [IsAuthenticated]

    def get(self, request: Request, pk: int) -> Response:
        username = _get_username(request)
        try:
            session = ChatSession.objects.get(id=pk, username=username)
        except ChatSession.DoesNotExist:
            return Response({"error": "Session not found."}, status=404)

        try:
            from django_ai_assistant.models import Message

            qs = (
                Message.objects.filter(thread_id=session.thread_id)
                .order_by("created_at")
                .values("role", "content", "created_at")
            )
            _role_map = {"human": "user", "ai": "assistant"}
            data = [
                {
                    "role": _role_map.get(m["role"], m["role"]),
                    "content": m["content"],
                    "created_at": m["created_at"].isoformat(),
                }
                for m in qs
            ]
        except Exception as exc:
            logger.debug("Could not load messages for session %s: %s", pk, exc)
            data = []

        return Response(data)


# ---------------------------------------------------------------------------
# Updated ChatAPIView — supports both legacy (sync) and session (async) modes
# ---------------------------------------------------------------------------

# Re-declare here to keep the class self-contained; original _run_assistant
# is still used for the legacy (no session_id) path.


class ChatAPIView(APIView):
    """
    POST /api/chat/

    Mode A — legacy (thread_id, no session_id):
        Request:  {"message": "…", "thread_id": null}
        Response: {"reply": "…", "thread_id": "uuid"}

    Mode B — session (with session_id):
        Request:  {"message": "…", "session_id": 42}
        Response: {"task_id": "celery-uuid", "session_id": 42,
                   "session_name": "…"}   (session_name set on first message)

        The frontend polls GET /api/chat/tasks/{task_id}/ to retrieve the reply.

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

        session_id = request.data.get("session_id")

        # ---- Mode B: session-based async path ----
        if session_id is not None:
            return self._handle_session_message(request, message, session_id)

        # ---- Mode A: legacy synchronous path ----
        thread_id: str | None = request.data.get("thread_id") or None

        user_label = getattr(request.user, "username", None) or str(
            getattr(request.user, "id", "anon")
        )
        logger.info(
            "Chat request (legacy)  user=%s  thread=%s  message=%r",
            user_label,
            thread_id or "(new)",
            message[:120],
        )

        t0 = time.monotonic()
        try:
            reply, thread_id = _run_assistant(message, thread_id, request)
        except RuntimeError as exc:
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
            "Chat response (legacy)  thread=%s  elapsed=%.1fs  reply_len=%d",
            thread_id,
            elapsed,
            len(reply),
        )

        return Response({"reply": reply, "thread_id": thread_id})

    def _handle_session_message(
        self, request: Request, message: str, session_id
    ) -> Response:
        username = _get_username(request)
        try:
            session = ChatSession.objects.get(id=session_id, username=username)
        except ChatSession.DoesNotExist:
            return Response({"error": "Session not found."}, status=404)

        # Auto-name session on first message (before dispatching task).
        session_name = session.name
        if not session_name:
            session_name = (message[:57] + "…") if len(message) > 57 else message
            session.name = session_name
            session.save(update_fields=["name", "updated_at"])

        logger.info(
            "Chat request (session)  user=%s  session=%s  thread=%s  message=%r",
            username,
            session_id,
            session.thread_id,
            message[:120],
        )

        from threat_intel.tasks import run_chat_task

        task = run_chat_task.delay(
            message,
            str(session.thread_id),
            session_id=session.id,
        )

        return Response(
            {
                "task_id": task.id,
                "session_id": session.id,
                "session_name": session_name,
            }
        )


# ---------------------------------------------------------------------------
# Task poll   GET /api/chat/tasks/{task_id}/
# ---------------------------------------------------------------------------


class ChatTaskStatusView(APIView):
    """
    GET /api/chat/tasks/{task_id}/

    Returns the current status of a Celery chat task.

    Response shapes:
        {"status": "running"}
        {"status": "complete", "reply": "…", "thread_id": "uuid"}
        {"status": "error",    "error":  "…"}
        {"status": "pending"}   — task_id unknown / cache miss
    """

    permission_classes = [IsAuthenticated]

    def get(self, request: Request, task_id: str) -> Response:
        from django.core.cache import cache

        result = cache.get(f"chat_task:{task_id}")
        if result is None:
            return Response({"status": "pending"})
        return Response(result)


# ---------------------------------------------------------------------------
# RAG status panel   GET /api/chat/rag-status/
# ---------------------------------------------------------------------------

# Models exposed via the DB tool (model title-case → app_label).
_RAG_DB_MODELS: dict[str, str] = {
    "Log": "logs",
    "Tag": "tags",
    "Operation": "operations",
    "EvidenceFile": "evidence",
    "LogTemplate": "templates_mgmt",
    "Relation": "relations",
}


def _chroma_collection_count(db_path: Path, collection_name: str) -> int | None:
    """Return the number of documents in a Chroma collection, or None on error."""
    try:
        import chromadb

        client = chromadb.PersistentClient(path=str(db_path))
        col = client.get_collection(collection_name)
        return col.count()
    except Exception:
        return None


def _jsonl_line_count(path: Path) -> int:
    """Count non-empty lines in a JSONL file."""
    try:
        return sum(1 for line in path.open() if line.strip())
    except Exception:
        return 0


def _check_vllm_online(base_url: str, timeout: float = 2.0) -> bool:
    """Probe vLLM /v1/models with a short timeout; return True if reachable."""
    try:
        import httpx

        resp = httpx.get(f"{base_url.rstrip('/')}/models", timeout=timeout)
        return resp.status_code == 200
    except Exception:
        return False


class RagStatusView(APIView):
    """
    GET /api/chat/rag-status/

    Returns live counts and sync timestamps for all RAG data sources.
    The frontend loads this once on page load and re-polls every 5 minutes.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        threat_data = Path(settings.BASE_DIR) / "threat_data"
        chroma_db = threat_data / "chroma_db"

        # ---- MITRE ATT&CK ----
        mitre_jsonl = threat_data / "mitre_techniques.jsonl"
        mitre_count: int = 0
        mitre_last_sync: str | None = None
        mitre_domains: dict[str, int] = {}

        if mitre_jsonl.exists():
            chroma_count = _chroma_collection_count(chroma_db, "mitre_techniques")
            mitre_count = chroma_count if chroma_count is not None else _jsonl_line_count(mitre_jsonl)
            mitre_last_sync = _mtime_iso(mitre_jsonl)
            # Domain breakdown from the Django DB (fast, no Chroma needed).
            for domain, cnt in (
                MitreTechnique.objects
                .values("domain")
                .annotate(cnt=Count("id"))
                .values_list("domain", "cnt")
            ):
                if domain:
                    mitre_domains[domain] = cnt

        # ---- NVD CVEs ----
        nvd_jsonl = threat_data / "nvd_cves.jsonl"
        nvd_count: int = 0
        nvd_last_sync: str | None = None
        cvss_dist: dict[str, int] = {"critical": 0, "high": 0, "medium": 0, "low": 0}

        if nvd_jsonl.exists():
            chroma_count = _chroma_collection_count(chroma_db, "nvd_cves")
            nvd_count = chroma_count if chroma_count is not None else _jsonl_line_count(nvd_jsonl)
            nvd_last_sync = _mtime_iso(nvd_jsonl)
            cvss_dist["critical"] = NvdCve.objects.filter(cvss_score__gte=9.0).count()
            cvss_dist["high"] = NvdCve.objects.filter(
                cvss_score__gte=7.0, cvss_score__lt=9.0
            ).count()
            cvss_dist["medium"] = NvdCve.objects.filter(
                cvss_score__gte=4.0, cvss_score__lt=7.0
            ).count()
            cvss_dist["low"] = NvdCve.objects.filter(
                cvss_score__isnull=False, cvss_score__lt=4.0
            ).count()

        # ---- Django DB models ----
        from django.apps import apps as django_apps

        db_models_data: list[dict] = []
        for model_title, app_label in _RAG_DB_MODELS.items():
            try:
                model_class = django_apps.get_model(app_label, model_title)
                cnt = model_class.objects.count()
                db_models_data.append({"name": model_title, "count": cnt})
            except Exception as exc:
                logger.debug("RAG status: could not count %s: %s", model_title, exc)

        # ---- vLLM status ----
        vllm_base_url: str = getattr(settings, "VLLM_BASE_URL", "http://localhost:8000/v1")
        llm_online = _check_vllm_online(vllm_base_url)

        return Response(
            {
                "mitre": {
                    "count": mitre_count,
                    "last_sync": mitre_last_sync,
                    "domains": mitre_domains,
                },
                "nvd": {
                    "count": nvd_count,
                    "last_sync": nvd_last_sync,
                    "cvss_distribution": cvss_dist,
                },
                "db_models": db_models_data,
                "llm_online": llm_online,
            }
        )


def _mtime_iso(path: Path) -> str | None:
    """Return the file modification time as an ISO 8601 string."""
    try:
        from datetime import datetime, timezone

        mtime = path.stat().st_mtime
        return datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat()
    except Exception:
        return None
