from rest_framework.routers import DefaultRouter
from templates_mgmt.views import LogTemplateViewSet

router = DefaultRouter()
router.register(r"templates", LogTemplateViewSet, basename="template")

urlpatterns = router.urls
