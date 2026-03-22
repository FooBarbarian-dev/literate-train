from rest_framework import serializers
from templates_mgmt.models import LogTemplate


class LogTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LogTemplate
        fields = ["id", "name", "template_data", "created_by", "created_at", "updated_at"]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]


class LogTemplateCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LogTemplate
        fields = ["name", "template_data"]
