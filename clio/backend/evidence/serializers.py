from rest_framework import serializers
from evidence.models import EvidenceFile


class EvidenceFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = EvidenceFile
        fields = [
            "id", "log", "filename", "original_filename", "file_type",
            "file_size", "upload_date", "uploaded_by", "description",
            "md5_hash", "filepath", "metadata",
        ]
        read_only_fields = [
            "id", "filename", "file_size", "upload_date", "uploaded_by",
            "md5_hash", "filepath",
        ]


class EvidenceFileCreateSerializer(serializers.Serializer):
    log_id = serializers.IntegerField()
    file = serializers.FileField()
    description = serializers.CharField(required=False, default="")


class EvidenceFileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EvidenceFile
        fields = ["description", "metadata"]
        extra_kwargs = {field: {"required": False} for field in fields}
