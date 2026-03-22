import hashlib
import secrets

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view

from accounts.permissions import IsJWTAuthenticated, IsAdmin
from api_keys.models import ApiKey
from api_keys.serializers import (
    ApiKeySerializer,
    ApiKeyCreateSerializer,
    ApiKeyGeneratedSerializer,
)


@extend_schema_view(
    list=extend_schema(summary="List API keys", tags=["api-keys"]),
    create=extend_schema(summary="Create an API key (admin only)", tags=["api-keys"]),
    retrieve=extend_schema(summary="Get an API key", tags=["api-keys"]),
    update=extend_schema(summary="Update an API key", tags=["api-keys"]),
    partial_update=extend_schema(summary="Partially update an API key", tags=["api-keys"]),
    destroy=extend_schema(summary="Delete an API key (admin only)", tags=["api-keys"]),
)
class ApiKeyViewSet(viewsets.ModelViewSet):
    serializer_class = ApiKeySerializer
    permission_classes = [IsJWTAuthenticated]

    def get_queryset(self):
        return ApiKey.objects.all().order_by("-created_at")

    def get_permissions(self):
        if self.action in ("create", "destroy"):
            return [IsAdmin()]
        return [IsJWTAuthenticated()]

    @extend_schema(
        request=ApiKeyCreateSerializer,
        responses={201: ApiKeyGeneratedSerializer},
        summary="Generate a new API key (admin only)",
        tags=["api-keys"],
    )
    @action(detail=False, methods=["post"], permission_classes=[IsAdmin])
    def generate(self, request):
        serializer = ApiKeyCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        # Generate key
        raw_key = secrets.token_urlsafe(48)
        key_id = secrets.token_urlsafe(16)
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

        api_key = ApiKey.objects.create(
            name=data["name"],
            key_id=key_id,
            key_hash=key_hash,
            created_by=request.user.username,
            permissions=data.get("permissions", ["logs:write"]),
            description=data.get("description", ""),
            expires_at=data.get("expires_at"),
            operation_id=data.get("operation_id"),
        )

        # Return raw key only this once
        response_data = ApiKeyGeneratedSerializer(api_key).data
        response_data["raw_key"] = raw_key

        return Response(response_data, status=status.HTTP_201_CREATED)

    @extend_schema(summary="Revoke an API key", tags=["api-keys"])
    @action(detail=True, methods=["post"])
    def revoke(self, request, pk=None):
        api_key = self.get_object()

        if not api_key.is_active:
            return Response(
                {"error": True, "message": "Key is already revoked"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        api_key.is_active = False
        api_key.save(update_fields=["is_active", "updated_at"])

        return Response(ApiKeySerializer(api_key).data)
