from rest_framework import serializers


class ExportFilterSerializer(serializers.Serializer):
    operation_id = serializers.IntegerField(required=False)
    start_date = serializers.DateTimeField(required=False)
    end_date = serializers.DateTimeField(required=False)
    tag_ids = serializers.CharField(required=False, help_text="Comma-separated tag IDs")
    fields = serializers.CharField(
        required=False,
        help_text="Comma-separated list of fields to include in the export. Defaults to all fields.",
    )
