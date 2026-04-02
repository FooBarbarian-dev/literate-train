from django.urls import path
from rest_framework.routers import DefaultRouter
from logs.views import LogViewSet
from logs.htmx_views import (
    logs_page,
    logs_list_htmx,
    log_panel,
    log_save_htmx,
    log_delete_htmx,
    log_toggle,
    card_fields_modal,
    log_ai_context_htmx,
)

app_name = "logs"

router = DefaultRouter()
router.register(r"api/logs", LogViewSet, basename="log-api")

urlpatterns = [
    path("", logs_page, name="logs-page"),
    path("htmx/list/", logs_list_htmx, name="logs-list-htmx"),
    path("htmx/panel/", log_panel, name="log-panel"),
    path("htmx/save/", log_save_htmx, name="log-save-htmx"),
    path("htmx/<int:log_id>/delete/", log_delete_htmx, name="log-delete-htmx"),
    path("htmx/<int:log_id>/toggle/", log_toggle, name="log-toggle"),
    path("htmx/card-fields/", card_fields_modal, name="card-fields-modal"),
    path("htmx/<int:log_id>/ai-context/", log_ai_context_htmx, name="log-ai-context-htmx"),
] + router.urls
