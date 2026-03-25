from rest_framework.routers import DefaultRouter
from templates_mgmt.views import LogTemplateViewSet

app_name = "templates_mgmt"

router = DefaultRouter()
router.register(r"templates", LogTemplateViewSet, basename="template")

urlpatterns = router.urls
