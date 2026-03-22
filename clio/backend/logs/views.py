import logging

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view
from django_filters.rest_framework import DjangoFilterBackend

from accounts.permissions import IsJWTAuthenticated, IsAdmin

logger = logging.getLogger("clio.logs")
from logs.filters import LogFilterSet
from logs.models import Log
from logs.serializers import LogCreateSerializer, LogUpdateSerializer, LogListSerializer
from logs.services import (
    create_log_with_encryption,
    update_log_with_encryption,
    toggle_lock,
    auto_tag_with_operation,
    get_active_operation_tag,
    check_log_lock,
)


@extend_schema_view(
    list=extend_schema(summary="List logs (operation-scoped)", tags=["logs"]),
    create=extend_schema(summary="Create a log entry", tags=["logs"]),
    retrieve=extend_schema(summary="Get a single log entry", tags=["logs"]),
    update=extend_schema(summary="Update a log entry", tags=["logs"]),
    partial_update=extend_schema(summary="Partially update a log entry", tags=["logs"]),
    destroy=extend_schema(summary="Delete a log entry (admin only)", tags=["logs"]),
)
class LogViewSet(viewsets.ModelViewSet):
    serializer_class = LogListSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = LogFilterSet
    permission_classes = [IsJWTAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Log.objects.prefetch_related("tags").all()

        active_op_tag_id = get_active_operation_tag(user.username)

        if user.is_admin and not active_op_tag_id:
            return qs
        if not active_op_tag_id:
            return qs.none()
        return qs.filter(log_tags__tag_id=active_op_tag_id).distinct()

    def get_serializer_class(self):
        if self.action == "create":
            return LogCreateSerializer
        if self.action in ("update", "partial_update"):
            return LogUpdateSerializer
        return LogListSerializer

    def perform_create(self, serializer):
        log = create_log_with_encryption(serializer, self.request.user)
        auto_tag_with_operation(log.id, self.request.user.username)
        serializer.instance = log
        logger.info("Log %d created by %s (host=%s)", log.id, self.request.user.username, log.hostname)

    def perform_update(self, serializer):
        log = self.get_object()
        if not check_log_lock(log, self.request.user.username, self.request.user.is_admin):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Log is locked by another user")

        data = serializer.validated_data
        update_log_with_encryption(log, data, self.request.user)

    def perform_destroy(self, instance):
        if not self.request.user.is_admin:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only admins can delete logs")
        logger.info("Log %d deleted by %s", instance.id, self.request.user.username)
        instance.delete()

    @extend_schema(summary="Toggle lock on a log entry", tags=["logs"])
    @action(detail=True, methods=["post"], url_path="toggle-lock")
    def toggle_lock(self, request, pk=None):
        log = self.get_object()
        try:
            log = toggle_lock(log, request.user.username, request.user.is_admin)
        except PermissionError as e:
            return Response(
                {"error": True, "message": str(e)},
                status=status.HTTP_403_FORBIDDEN,
            )
        logger.info("Log %d lock toggled by %s (locked=%s)", log.id, request.user.username, log.locked)
        return Response(LogListSerializer(log).data)

    @extend_schema(summary="Bulk delete logs (admin only)", tags=["logs"])
    @action(detail=False, methods=["post"], url_path="bulk-delete", permission_classes=[IsAdmin])
    def bulk_delete(self, request):
        ids = request.data.get("ids", [])
        if not ids:
            return Response(
                {"error": True, "message": "No IDs provided"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        deleted_count = Log.objects.filter(id__in=ids).delete()[0]
        logger.warning("Bulk delete: %d logs deleted by %s", deleted_count, request.user.username)
        return Response({"deleted": deleted_count})
