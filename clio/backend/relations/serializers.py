from rest_framework import serializers

from relations.models import (
    FileStatus,
    FileStatusHistory,
    LogRelationship,
    Relation,
    TagRelationship,
)


class RelationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Relation
        fields = "__all__"
        read_only_fields = ("id", "first_seen", "last_seen")


class RelationBulkItemSerializer(serializers.ModelSerializer):
    """Serializer used for individual items inside the bulk_ingest payload."""

    class Meta:
        model = Relation
        fields = "__all__"
        read_only_fields = ("id", "first_seen", "last_seen")


class LogRelationshipSerializer(serializers.ModelSerializer):
    class Meta:
        model = LogRelationship
        fields = "__all__"
        read_only_fields = ("id", "created_at")


class TagRelationshipSerializer(serializers.ModelSerializer):
    class Meta:
        model = TagRelationship
        fields = "__all__"
        read_only_fields = ("id", "first_seen", "last_seen")


class FileStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileStatus
        fields = "__all__"
        read_only_fields = ("id", "first_seen", "last_seen")


class FileStatusUpsertSerializer(serializers.ModelSerializer):
    """Serializer for the upsert action. filename is required; hostname and internal_ip default to empty string."""

    class Meta:
        model = FileStatus
        fields = "__all__"
        read_only_fields = ("id", "first_seen", "last_seen")
        extra_kwargs = {
            "filename": {"required": True},
        }


class FileStatusHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = FileStatusHistory
        fields = "__all__"
        read_only_fields = ("id", "timestamp")
