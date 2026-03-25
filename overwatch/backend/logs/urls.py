from rest_framework.routers import DefaultRouter
from logs.views import LogViewSet

app_name = "logs"

router = DefaultRouter()
router.register(r"logs", LogViewSet, basename="log")

urlpatterns = router.urls
