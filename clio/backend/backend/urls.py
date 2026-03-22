"""
Root URL configuration for the Clio platform.
"""

from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    # API schema & docs
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/schema/swagger/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/schema/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
    # App URLs
    path("api/accounts/", include("accounts.urls")),
    path("api/logs/", include("logs.urls")),
    path("api/tags/", include("tags.urls")),
    path("api/operations/", include("operations.urls")),
    path("api/evidence/", include("evidence.urls")),
    path("api/api-keys/", include("api_keys.urls")),
    path("api/ingest/", include("ingest.urls")),
    path("api/export/", include("export.urls")),
    path("api/sessions/", include("sessions_mgmt.urls")),
    path("api/templates/", include("templates_mgmt.urls")),
    path("api/audit/", include("audit.urls")),
]
