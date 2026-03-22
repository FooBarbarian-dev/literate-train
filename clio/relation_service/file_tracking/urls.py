from django.urls import include, path
from rest_framework.routers import DefaultRouter

from file_tracking.views import FileStatusHistoryViewSet, FileStatusViewSet

router = DefaultRouter()
router.register(r"file-status", FileStatusViewSet, basename="filestatus")
router.register(r"file-status-history", FileStatusHistoryViewSet, basename="filestatushistory")

urlpatterns = [
    path("", include(router.urls)),
]
