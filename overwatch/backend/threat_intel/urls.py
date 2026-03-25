from django.urls import path

from threat_intel.views import (
    ChatAPIView,
    ChatSessionDetailView,
    ChatSessionListCreateView,
    ChatSessionMessagesView,
    ChatTaskStatusView,
    MitreFacetsView,
    MitreTechniqueListView,
    NvdCveListView,
    RagStatusView,
)

app_name = "threat_intel"

urlpatterns = [
    # Original endpoints (unchanged)
    path("api/chat/", ChatAPIView.as_view(), name="threat-intel-chat-api"),
    path("api/threat-intel/mitre/", MitreTechniqueListView.as_view(), name="mitre-list"),
    path("api/threat-intel/mitre/facets/", MitreFacetsView.as_view(), name="mitre-facets"),
    path("api/threat-intel/cves/", NvdCveListView.as_view(), name="cve-list"),
    # Session management
    path("api/chat/sessions/", ChatSessionListCreateView.as_view(), name="chat-sessions"),
    path("api/chat/sessions/<int:pk>/", ChatSessionDetailView.as_view(), name="chat-session-detail"),
    path("api/chat/sessions/<int:pk>/messages/", ChatSessionMessagesView.as_view(), name="chat-session-messages"),
    # Celery task polling
    path("api/chat/tasks/<str:task_id>/", ChatTaskStatusView.as_view(), name="chat-task-status"),
    # RAG context panel data
    path("api/chat/rag-status/", RagStatusView.as_view(), name="rag-status"),
]
