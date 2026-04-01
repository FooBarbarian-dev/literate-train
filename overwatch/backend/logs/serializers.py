from rest_framework import serializers
from logs.models import Log
from logs import models
from logs.encryption import decrypt_field
from accounts.validators import validate_ip_address, normalize_mac_address


class TagBriefSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    color = serializers.CharField()
    category = serializers.CharField(allow_null=True)
    description = serializers.CharField(allow_blank=True, default="")


class LogCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Log
        fields = [
            "timestamp", "internal_ip", "external_ip", "mac_address",
            "hostname", "domain", "username", "command", "notes",
            "filename", "status", "secrets", "hash_algorithm", "hash_value", "pid",
        ]
        extra_kwargs = {
            "timestamp": {"required": False},
        }

    def validate_internal_ip(self, value):
        if value:
            validate_ip_address(value)
        return value

    def validate_external_ip(self, value):
        if value:
            validate_ip_address(value)
        return value

    def validate_mac_address(self, value):
        if value:
            return normalize_mac_address(value)
        return value

    def validate_command(self, value):
        if value and len(value) > 254:
            raise serializers.ValidationError("Command must be 254 characters or fewer.")
        return value

    def validate_notes(self, value):
        if value and len(value) > 254:
            raise serializers.ValidationError("Notes must be 254 characters or fewer.")
        return value


class LogUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Log
        fields = [
            "timestamp", "internal_ip", "external_ip", "mac_address",
            "hostname", "domain", "username", "command", "notes",
            "filename", "status", "secrets", "hash_algorithm", "hash_value", "pid",
        ]
        extra_kwargs = {field: {"required": False} for field in fields}

    def validate_internal_ip(self, value):
        if value:
            validate_ip_address(value)
        return value

    def validate_external_ip(self, value):
        if value:
            validate_ip_address(value)
        return value

    def validate_mac_address(self, value):
        if value:
            return normalize_mac_address(value)
        return value


class LogListSerializer(serializers.ModelSerializer):
    tags = TagBriefSerializer(many=True, read_only=True)
    secrets = serializers.SerializerMethodField()

    class Meta:
        model = Log
        fields = "__all__"

    def get_secrets(self, obj):
        if obj.secrets:
            return decrypt_field(obj.secrets)
        return None

class LogAIContextSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.LogAIContextSource
        fields = ["source_type", "record_id", "source_url"]

class LogAIContextSerializer(serializers.ModelSerializer):
    sources = LogAIContextSourceSerializer(many=True, read_only=True)

    class Meta:
        model = models.LogAIContext
        fields = [
            "id", "status", "generated_at", "summary",
            "mitre_techniques", "cves", "sources", "error_message"
        ]
