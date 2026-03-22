import logging

from django.db.models import Count
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view

from accounts.permissions import IsJWTAuthenticated, IsAdmin

logger = logging.getLogger("clio.operations")
from operations.models import Operation, UserOperation
from operations.serializers import (
    OperationSerializer,
    OperationCreateSerializer,
    UserOperationSerializer,
    AssignUserSerializer,
    SetActiveOperationSerializer,
)
from operations.services import (
    create_operation,
    assign_user_to_operation,
    remove_user_from_operation,
    set_active_operation,
    get_user_operations,
)


@extend_schema_view(
    list=extend_schema(summary="List all operations", tags=["operations"]),
    create=extend_schema(summary="Create an operation (admin only)", tags=["operations"]),
    retrieve=extend_schema(summary="Get an operation", tags=["operations"]),
    update=extend_schema(summary="Update an operation (admin only)", tags=["operations"]),
    partial_update=extend_schema(summary="Partially update an operation", tags=["operations"]),
    destroy=extend_schema(summary="Deactivate an operation (admin only)", tags=["operations"]),
)
class OperationViewSet(viewsets.ModelViewSet):
    serializer_class = OperationSerializer
    permission_classes = [IsJWTAuthenticated]

    def get_queryset(self):
        return Operation.objects.filter(is_active=True).select_related("tag").annotate(
            user_count=Count("useroperation")
        )

    def get_serializer_class(self):
        if self.action == "create":
            return OperationCreateSerializer
        return OperationSerializer

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsAdmin()]
        return [IsJWTAuthenticated()]

    def perform_create(self, serializer):
        op = create_operation(
            name=serializer.validated_data["name"],
            description=serializer.validated_data.get("description", ""),
            created_by=self.request.user.username,
        )
        serializer.instance = op
        logger.info("Operation '%s' created by %s", op.name, self.request.user.username)

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=["is_active", "updated_at"])

    @extend_schema(summary="Get my operations", tags=["operations"])
    @action(detail=False, methods=["get"], url_path="my-operations")
    def my_operations(self, request):
        user_ops = get_user_operations(request.user.username)
        serializer = UserOperationSerializer(user_ops, many=True)

        from common.redis_client import get_encrypted_redis
        redis_client = get_encrypted_redis()
        active_op_id = redis_client.get(f"user:{request.user.username}:active_operation")

        data = serializer.data
        for item in data:
            item["is_active"] = str(item["operation_id"]) == active_op_id

        return Response(data)

    @extend_schema(
        request=SetActiveOperationSerializer,
        summary="Set active operation",
        tags=["operations"],
    )
    @action(detail=False, methods=["post"], url_path="set-active")
    def set_active(self, request):
        serializer = SetActiveOperationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        success = set_active_operation(
            request.user.username, serializer.validated_data["operation_id"]
        )
        if not success:
            return Response(
                {"error": True, "message": "Operation not found or not assigned"},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response({"message": "Active operation updated"})

    @extend_schema(
        request=AssignUserSerializer,
        summary="Assign user to operation (admin only)",
        tags=["operations"],
    )
    @action(detail=False, methods=["post"], url_path="assign-user", permission_classes=[IsAdmin])
    def assign_user(self, request):
        serializer = AssignUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_op = assign_user_to_operation(
            username=serializer.validated_data["username"],
            operation_id=serializer.validated_data["operation_id"],
            assigned_by=request.user.username,
            is_primary=serializer.validated_data.get("is_primary", False),
        )
        logger.info("User '%s' assigned to operation %d by %s",
                    serializer.validated_data["username"],
                    serializer.validated_data["operation_id"],
                    request.user.username)
        return Response(UserOperationSerializer(user_op).data, status=201)

    @extend_schema(summary="Remove user from operation (admin only)", tags=["operations"])
    @action(detail=False, methods=["post"], url_path="remove-user", permission_classes=[IsAdmin])
    def remove_user(self, request):
        username = request.data.get("username")
        operation_id = request.data.get("operation_id")

        if not username or not operation_id:
            return Response(
                {"error": True, "message": "username and operation_id required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        success = remove_user_from_operation(username, int(operation_id))
        if not success:
            return Response(
                {"error": True, "message": "Assignment not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response({"message": "User removed from operation"})
