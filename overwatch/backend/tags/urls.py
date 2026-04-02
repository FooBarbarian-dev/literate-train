from django.urls import path
from rest_framework.routers import DefaultRouter
from tags.views import TagViewSet
from tags.htmx_views import (
    tags_page,
    tags_list_htmx,
    create_tag_modal,
    create_tag_htmx,
)

app_name = "tags"

router = DefaultRouter()
router.register(r"api/tags", TagViewSet, basename="tag-api")

urlpatterns = [
    path("", tags_page, name="tags-page"),
    path("htmx/list/", tags_list_htmx, name="tags-list-htmx"),
    path("htmx/create/modal/", create_tag_modal, name="create-tag-modal"),
    path("htmx/create/", create_tag_htmx, name="create-tag-htmx"),
] + router.urls
