from django.urls import include, path
from rest_framework.routers import DefaultRouter

from relations.views import (
    FileStatusHistoryViewSet,
    FileStatusViewSet,
    LogRelationshipViewSet,
    RelationViewSet,
    TagRelationshipViewSet,
)

app_name = "relations"

router = DefaultRouter()
router.register(r"relations", RelationViewSet, basename="relation")
router.register(r"log-relationships", LogRelationshipViewSet, basename="logrelationship")
router.register(r"tag-relationships", TagRelationshipViewSet, basename="tagrelationship")
router.register(r"file-status", FileStatusViewSet, basename="filestatus")
router.register(r"file-status-history", FileStatusHistoryViewSet, basename="filestatushistory")

from relations.htmx_views import relations_page, relations_graph_htmx

urlpatterns = [
    path("", relations_page, name="relations-page"),
    path("htmx/graph/", relations_graph_htmx, name="relations-graph-htmx"),
] + router.urls
