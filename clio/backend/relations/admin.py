from django.contrib import admin

from relations.models import (
    FileStatus,
    FileStatusHistory,
    LogRelationship,
    Relation,
    TagRelationship,
)


@admin.register(Relation)
class RelationAdmin(admin.ModelAdmin):
    list_display = (
        "source_type", "source_value", "target_type", "target_value",
        "pattern_type", "strength", "connection_count", "last_seen",
    )
    list_filter = ("source_type", "target_type", "pattern_type")
    search_fields = ("source_value", "target_value")
    readonly_fields = ("first_seen", "last_seen")


@admin.register(LogRelationship)
class LogRelationshipAdmin(admin.ModelAdmin):
    list_display = ("source_id", "target_id", "type", "relationship", "created_by", "created_at")
    list_filter = ("type", "created_at")
    search_fields = ("relationship", "notes", "created_by")
    readonly_fields = ("created_at",)


@admin.register(TagRelationship)
class TagRelationshipAdmin(admin.ModelAdmin):
    list_display = (
        "source_tag_id", "target_tag_id",
        "cooccurrence_count", "sequence_count", "correlation_strength",
        "last_seen",
    )
    list_filter = ("last_seen",)
    readonly_fields = ("first_seen", "last_seen")


@admin.register(FileStatus)
class FileStatusAdmin(admin.ModelAdmin):
    list_display = (
        "filename", "hostname", "internal_ip", "status",
        "hash_algorithm", "username", "analyst", "last_seen",
    )
    list_filter = ("status", "hostname", "hash_algorithm")
    search_fields = ("filename", "hostname", "username", "analyst", "hash_value")
    readonly_fields = ("first_seen", "last_seen")


@admin.register(FileStatusHistory)
class FileStatusHistoryAdmin(admin.ModelAdmin):
    list_display = (
        "filename", "hostname", "previous_status", "status",
        "username", "analyst", "timestamp",
    )
    list_filter = ("status", "previous_status", "hostname")
    search_fields = ("filename", "hostname", "username", "analyst")
    readonly_fields = ("timestamp",)
