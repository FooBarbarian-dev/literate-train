from django.urls import include, path
from rest_framework.routers import DefaultRouter

app_name = "relations"

from relations.views import (
    LogRelationshipViewSet,
    RelationViewSet,
    TagRelationshipViewSet,
    health_check,
)

router = DefaultRouter()
router.register(r"relations", RelationViewSet, basename="relation")
router.register(r"log-relationships", LogRelationshipViewSet, basename="logrelationship")
router.register(r"tag-relationships", TagRelationshipViewSet, basename="tagrelationship")

urlpatterns = [
    path("health/", health_check, name="health-check"),
    path("", include(router.urls)),
]
