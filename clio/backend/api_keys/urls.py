from rest_framework.routers import DefaultRouter
from api_keys.views import ApiKeyViewSet

router = DefaultRouter()
router.register(r"api-keys", ApiKeyViewSet, basename="api-key")

urlpatterns = router.urls
