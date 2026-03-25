from django.urls import path

from threat_intel.views import ChatAPIView

app_name = "threat_intel"

urlpatterns = [
    path("api/chat/", ChatAPIView.as_view(), name="threat-intel-chat-api"),
]
