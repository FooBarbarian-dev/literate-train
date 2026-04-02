from django.urls import path

from threat_intel.views import (
    ChatAPIView,
    ChatSessionDetailView,
    ChatSessionListCreateView,
    ChatSessionMessagesView,
    ChatSessionSourcesView,
    ChatTaskStatusView,
    MitreFacetsView,
    MitreTechniqueListView,
    NvdCveListView,
    RagStatusView,
)

app_name = "threat_intel"

from threat_intel.htmx_views import (
    threat_intel_page,
    mitre_tab,
    cves_tab,
    assistant_tab,
    mitre_list_htmx,
    cves_list_htmx,
    chat_sessions_list,
    chat_session_create,
    chat_session_load,
    chat_session_messages_htmx,
    chat_send_message,
    chat_poll_task,
    rag_panel_htmx,
)

urlpatterns = [
    # UI Routes
    path("", threat_intel_page, name="threat-intel-page"),
    path("htmx/mitre/", mitre_tab, name="mitre-tab"),
    path("htmx/cves/", cves_tab, name="cves-tab"),
    path("htmx/assistant/", assistant_tab, name="assistant-tab"),
    path("htmx/mitre/list/", mitre_list_htmx, name="mitre-list-htmx"),
    path("htmx/cves/list/", cves_list_htmx, name="cves-list-htmx"),

    path("htmx/chat/sessions/", chat_sessions_list, name="chat-sessions-list"),
    path("htmx/chat/sessions/create/", chat_session_create, name="chat-session-create"),
    path("htmx/chat/sessions/<int:session_id>/", chat_session_load, name="chat-session-load"),
    path("htmx/chat/sessions/<int:session_id>/messages/", chat_session_messages_htmx, name="chat-session-messages-htmx"),
    path("htmx/chat/sessions/<int:session_id>/send/", chat_send_message, name="chat-send-message"),
    path("htmx/chat/sessions/<int:session_id>/poll/<str:task_id>/", chat_poll_task, name="chat-poll-task"),
    path("htmx/rag-panel/", rag_panel_htmx, name="rag-panel-htmx"),

    # Original endpoints (unchanged)
    path("api/chat/", ChatAPIView.as_view(), name="threat-intel-chat-api"),
    path("api/threat-intel/mitre/", MitreTechniqueListView.as_view(), name="mitre-list"),
    path("api/threat-intel/mitre/facets/", MitreFacetsView.as_view(), name="mitre-facets"),
    path("api/threat-intel/cves/", NvdCveListView.as_view(), name="cve-list"),
    # Session management
    path("api/chat/sessions/", ChatSessionListCreateView.as_view(), name="chat-sessions"),
    path("api/chat/sessions/<int:pk>/", ChatSessionDetailView.as_view(), name="chat-session-detail"),
    path("api/chat/sessions/<int:pk>/messages/", ChatSessionMessagesView.as_view(), name="chat-session-messages"),
    path("api/chat/sessions/<int:pk>/sources/", ChatSessionSourcesView.as_view(), name="chat-session-sources"),
    # Celery task polling
    path("api/chat/tasks/<str:task_id>/", ChatTaskStatusView.as_view(), name="chat-task-status"),
    # RAG context panel data
    path("api/chat/rag-status/", RagStatusView.as_view(), name="rag-status"),
]
