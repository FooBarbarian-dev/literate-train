from rest_framework import serializers


class LogEntryIngestSerializer(serializers.Serializer):
    timestamp = serializers.DateTimeField(required=False)
    internal_ip = serializers.CharField(required=False, default="")
    external_ip = serializers.CharField(required=False, default="")
    mac_address = serializers.CharField(required=False, default="")
    hostname = serializers.CharField(required=False, default="")
    domain = serializers.CharField(required=False, default="")
    username = serializers.CharField(required=False, default="")
    command = serializers.CharField(required=False, default="")
    notes = serializers.CharField(required=False, default="")
    filename = serializers.CharField(required=False, default="")
    status = serializers.CharField(required=False, default="")
    secrets = serializers.CharField(required=False, default="")
    hash_algorithm = serializers.CharField(required=False, default="")
    hash_value = serializers.CharField(required=False, default="")
    pid = serializers.CharField(required=False, default="")


class BulkIngestSerializer(serializers.Serializer):
    entries = LogEntryIngestSerializer(many=True)


class BulkIngestResultSerializer(serializers.Serializer):
    created = serializers.IntegerField()
    errors = serializers.ListField(child=serializers.DictField())
