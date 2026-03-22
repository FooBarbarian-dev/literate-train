from rest_framework import serializers

from relations.models import LogRelationship, Relation, TagRelationship


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
