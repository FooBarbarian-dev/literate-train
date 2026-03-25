from rest_framework.routers import DefaultRouter
from api_keys.views import ApiKeyViewSet

app_name = "api_keys"

router = DefaultRouter()
router.register(r"", ApiKeyViewSet, basename="api-key")

urlpatterns = router.urls
