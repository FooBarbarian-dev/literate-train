"""
Root URL configuration for the Overwatch platform.
"""

import time

from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    return Response({"status": "ok", "timestamp": time.time()})


urlpatterns = [
    path("admin/", admin.site.urls),
    # Top-level health check (used by Docker healthcheck)
    path("api/health/", health_check, name="health-check"),
    # API schema & docs (public, no auth or throttle required)
    path(
        "api/schema/",
        SpectacularAPIView.as_view(permission_classes=[AllowAny], throttle_classes=[]),
        name="schema",
    ),
    path(
        "api/schema/swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="schema", permission_classes=[AllowAny], throttle_classes=[]),
        name="swagger-ui",
    ),
    path(
        "api/schema/redoc/",
        SpectacularRedocView.as_view(url_name="schema", permission_classes=[AllowAny], throttle_classes=[]),
        name="redoc",
    ),
    # App URLs
    # Base HTMX/UI Paths (namespaced by their app automatically from app_name in urls.py)
    path("accounts/", include("accounts.urls")),
    path("operations/", include("operations.urls")),
    path("tags/", include("tags.urls")),
    path("relationships/", include("relations.urls")),
    path("logs/", include("logs.urls")),
    path("api_keys/", include("api_keys.urls")),
    path("export/", include("export.urls")),
    path("threat-intel/", include("threat_intel.urls")),
    # Mapping ChatPage equivalent natively
    path("chat/", include("threat_intel.urls")),

    # Base API Paths
    # Since we prefix 'api/' here, but don't define a unique API urls file, DRF routers
    # attached to the same URLs file are duplicated.
    # To isolate API routing without namespace collisions and 404s, we will assign
    # dynamic API namespaces or just accept that the UI paths include the DRF endpoints.
    # Because we're mixing UI/API in the same file, the paths already exist under "accounts/", etc.
    # If the frontend tries to call /api/accounts/..., we will include the same urls but with an "api_" namespace.
    path("api/accounts/", include(("accounts.urls", "accounts"), namespace="api_accounts")),
    path("api/logs/", include(("logs.urls", "logs"), namespace="api_logs")),
    path("api/tags/", include(("tags.urls", "tags"), namespace="api_tags")),
    path("api/operations/", include(("operations.urls", "operations"), namespace="api_operations")),
    path("api/evidence/", include(("evidence.urls", "evidence"), namespace="api_evidence")),
    path("api/api-keys/", include(("api_keys.urls", "api_keys"), namespace="api_api_keys")),
    path("api/ingest/", include(("ingest.urls", "ingest"), namespace="api_ingest")),
    path("api/export/", include(("export.urls", "export"), namespace="api_export")),
    path("api/sessions/", include(("sessions_mgmt.urls", "sessions_mgmt"), namespace="api_sessions")),
    path("api/templates/", include(("templates_mgmt.urls", "templates_mgmt"), namespace="api_templates")),
    path("api/audit/", include(("audit.urls", "audit"), namespace="api_audit")),
    path("api/relations/", include(("relations.urls", "relations"), namespace="api_relations")),
    path("api/threat-intel/", include(("threat_intel.urls", "threat_intel"), namespace="api_threat_intel")),

    # Catch-all
    path("", include("logs.urls")), # Root goes to logs initially, or dashboard
]
