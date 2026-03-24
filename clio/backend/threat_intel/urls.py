from django.urls import path

from threat_intel.views import ChatAPIView

urlpatterns = [
    path("api/chat/", ChatAPIView.as_view(), name="threat-intel-chat-api"),
]
