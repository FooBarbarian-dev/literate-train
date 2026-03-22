from rest_framework.routers import DefaultRouter
from operations.views import OperationViewSet

router = DefaultRouter()
router.register(r"operations", OperationViewSet, basename="operation")

urlpatterns = router.urls
