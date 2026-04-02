from django.urls import path
from rest_framework.routers import DefaultRouter
from api_keys.views import ApiKeyViewSet
from api_keys.htmx_views import generate_key_htmx, revoke_keys_htmx

app_name = "api_keys"

router = DefaultRouter()
router.register(r"api-keys", ApiKeyViewSet, basename="apikey")

urlpatterns = [
    path("htmx/generate/", generate_key_htmx, name="generate-key-htmx"),
    path("htmx/revoke-all/", revoke_keys_htmx, name="revoke-keys-htmx"),
] + router.urls
