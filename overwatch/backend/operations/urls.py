from django.urls import path
from rest_framework.routers import DefaultRouter
from operations.views import OperationViewSet
from operations.htmx_views import (
    operations_page,
    operations_list_htmx,
    create_operation_modal,
    create_operation_htmx,
    set_active_htmx,
)

app_name = "operations"

router = DefaultRouter()
router.register(r"operations", OperationViewSet, basename="operation")

urlpatterns = [
    # HTMX UI Routes
    path("", operations_page, name="operations-page"),
    path("htmx/list/", operations_list_htmx, name="operations-list-htmx"),
    path("htmx/create/modal/", create_operation_modal, name="create-operation-modal"),
    path("htmx/create/", create_operation_htmx, name="create-operation-htmx"),
    path("htmx/<int:operation_id>/set-active/", set_active_htmx, name="set-active-htmx"),
] + router.urls
