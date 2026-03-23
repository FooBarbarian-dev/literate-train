"""
URL patterns for the threat_intel app.

Included into the root urls.py as:
    path("", include("threat_intel.urls"))
    path("api/chat/", include("threat_intel.urls"))   # handled inside

Exposes:
    GET  /chat/      — standalone chat UI template
    POST /api/chat/  — JSON chat endpoint
"""

from django.urls import path

from threat_intel.views import ChatAPIView, ChatTemplateView

urlpatterns = [
    path("chat/", ChatTemplateView.as_view(), name="threat-intel-chat"),
    path("api/chat/", ChatAPIView.as_view(), name="threat-intel-chat-api"),
]
