from rest_framework import serializers

from relations.models import FileStatus, FileStatusHistory


class FileStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileStatus
        fields = "__all__"
        read_only_fields = ("id", "first_seen", "last_seen")


class FileStatusUpsertSerializer(serializers.ModelSerializer):
    """Serializer for the upsert action. filename, hostname, and internal_ip are required."""

    class Meta:
        model = FileStatus
        fields = "__all__"
        read_only_fields = ("id", "first_seen", "last_seen")
        extra_kwargs = {
            "filename": {"required": True},
            "hostname": {"required": True},
            "internal_ip": {"required": True},
        }


class FileStatusHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = FileStatusHistory
        fields = "__all__"
        read_only_fields = ("id", "timestamp")
