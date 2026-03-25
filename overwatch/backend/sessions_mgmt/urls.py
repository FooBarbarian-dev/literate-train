from django.urls import path
from sessions_mgmt.views import SessionListView, SessionTerminateView

app_name = "sessions_mgmt"

urlpatterns = [
    path("", SessionListView.as_view(), name="session-list"),
    path("terminate/", SessionTerminateView.as_view(), name="session-terminate"),
]
