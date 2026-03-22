from rest_framework import serializers
from operations.models import Operation, UserOperation


class OperationSerializer(serializers.ModelSerializer):
    tag_name = serializers.CharField(source="tag.name", read_only=True, default=None)
    tag_color = serializers.CharField(source="tag.color", read_only=True, default=None)
    user_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Operation
        fields = [
            "id", "name", "description", "tag_id", "tag_name", "tag_color",
            "is_active", "created_by", "created_at", "updated_at", "user_count",
        ]
        read_only_fields = ["id", "tag_id", "created_at", "updated_at"]


class OperationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Operation
        fields = ["name", "description"]


class UserOperationSerializer(serializers.ModelSerializer):
    operation_name = serializers.CharField(source="operation.name", read_only=True)
    operation_description = serializers.CharField(source="operation.description", read_only=True)
    tag_id = serializers.IntegerField(source="operation.tag_id", read_only=True)
    tag_name = serializers.SerializerMethodField()
    tag_color = serializers.SerializerMethodField()

    class Meta:
        model = UserOperation
        fields = [
            "id", "username", "operation_id", "operation_name", "operation_description",
            "is_primary", "assigned_by", "assigned_at", "last_accessed",
            "tag_id", "tag_name", "tag_color",
        ]

    def get_tag_name(self, obj):
        tag = getattr(obj.operation, "tag", None)
        return tag.name if tag else None

    def get_tag_color(self, obj):
        tag = getattr(obj.operation, "tag", None)
        return tag.color if tag else None


class AssignUserSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=100)
    operation_id = serializers.IntegerField()
    is_primary = serializers.BooleanField(default=False)


class SetActiveOperationSerializer(serializers.Serializer):
    operation_id = serializers.IntegerField()
