from rest_framework import serializers
from api_keys.models import ApiKey


class ApiKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = ApiKey
        fields = [
            "id", "name", "key_id", "created_by", "permissions", "description",
            "created_at", "updated_at", "expires_at", "is_active", "last_used",
            "metadata", "operation",
        ]
        read_only_fields = [
            "id", "key_id", "created_by", "created_at", "updated_at",
            "last_used",
        ]


class ApiKeyCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    permissions = serializers.JSONField(required=False, default=lambda: ["logs:write"])
    description = serializers.CharField(required=False, default="")
    expires_at = serializers.DateTimeField(required=False, allow_null=True, default=None)
    operation_id = serializers.IntegerField(required=False, allow_null=True, default=None)


class ApiKeyGeneratedSerializer(serializers.ModelSerializer):
    """Includes the raw key - only returned once at creation time."""
    raw_key = serializers.CharField(read_only=True)

    class Meta:
        model = ApiKey
        fields = [
            "id", "name", "key_id", "raw_key", "created_by", "permissions",
            "description", "created_at", "expires_at", "is_active", "operation",
        ]
