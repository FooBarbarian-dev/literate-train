from rest_framework.routers import DefaultRouter
from tags.views import TagViewSet

app_name = "tags"

router = DefaultRouter()
router.register(r"tags", TagViewSet, basename="tag")

urlpatterns = router.urls
