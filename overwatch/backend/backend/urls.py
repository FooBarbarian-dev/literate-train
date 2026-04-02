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
    path("accounts/", include(("accounts.urls", "accounts"), namespace="accounts")),
    path("operations/", include(("operations.urls", "operations"), namespace="operations")),
    path("tags/", include(("tags.urls", "tags"), namespace="tags")),
    path("relationships/", include(("relations.urls", "relations"), namespace="relations")),
    path("logs/", include(("logs.urls", "logs"), namespace="logs")),
    path("api/accounts/", include("accounts.urls")),
    path("api/logs/", include("logs.urls")),
    path("api/tags/", include("tags.urls")),
    path("api/operations/", include("operations.urls")),
    path("api/evidence/", include("evidence.urls")),
    path("api_keys/", include(("api_keys.urls", "api_keys"), namespace="api_keys")),
    path("api/api-keys/", include("api_keys.urls")),
    path("export/", include(("export.urls", "export"), namespace="export")),
    path("api/ingest/", include("ingest.urls")),
    path("api/export/", include("export.urls")),
    path("api/sessions/", include("sessions_mgmt.urls")),
    path("api/templates/", include("templates_mgmt.urls")),
    path("api/audit/", include("audit.urls")),
    path("api/relations/", include("relations.urls")),
    # Threat Intel: chat UI + API
    path("threat-intel/", include(("threat_intel.urls", "threat_intel"), namespace="threat_intel")),
    path("chat/", include(("threat_intel.urls", "chat"), namespace="chat")), # Mapping ChatPage equivalent
    path("", include("threat_intel.urls")),
]
