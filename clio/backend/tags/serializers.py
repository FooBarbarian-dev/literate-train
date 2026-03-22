from rest_framework import serializers
from tags.models import Tag, LogTag


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name", "color", "category", "description", "is_default", "created_by", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class TagCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["name", "color", "category", "description"]

    def validate_name(self, value):
        return value.strip().lower()

    def validate_color(self, value):
        import re
        if value and not re.match(r"^#[0-9A-Fa-f]{6}$", value):
            raise serializers.ValidationError("Color must be a valid hex color code (#RRGGBB)")
        return value


class TagStatsSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    color = serializers.CharField()
    category = serializers.CharField(allow_null=True)
    is_default = serializers.BooleanField()
    created_by = serializers.CharField(allow_null=True)
    usage_count = serializers.IntegerField()
    last_used = serializers.DateTimeField(allow_null=True)


class LogTagSerializer(serializers.ModelSerializer):
    tag_name = serializers.CharField(source="tag.name", read_only=True)
    tag_color = serializers.CharField(source="tag.color", read_only=True)

    class Meta:
        model = LogTag
        fields = ["id", "log_id", "tag_id", "tag_name", "tag_color", "tagged_by", "tagged_at"]
        read_only_fields = ["id", "tagged_at"]
