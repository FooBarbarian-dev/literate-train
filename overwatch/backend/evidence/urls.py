from rest_framework.routers import DefaultRouter
from evidence.views import EvidenceFileViewSet

app_name = "evidence"

router = DefaultRouter()
router.register(r"evidence", EvidenceFileViewSet, basename="evidence")

urlpatterns = router.urls
