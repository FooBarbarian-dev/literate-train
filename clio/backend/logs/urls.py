from rest_framework.routers import DefaultRouter
from logs.views import LogViewSet

router = DefaultRouter()
router.register(r"logs", LogViewSet, basename="log")

urlpatterns = router.urls
