# UX Audit 2026-03-23 — Changes:
#   RelationAdmin:
#     - source_value / target_value truncated to 60 chars (TextFields can be huge)
#     - date_hierarchy on last_seen; ordering = ("-connection_count",)
#   LogRelationshipAdmin:
#     - source_id / target_id rendered as clickable links to the Log change page
#     - date_hierarchy on created_at; ordering = ("-created_at",)
#   TagRelationshipAdmin:
#     - search_fields added (was missing entirely)
#     - date_hierarchy on last_seen; ordering = ("-cooccurrence_count",)
#   FileStatusAdmin:
#     - status_badge: color-coded pill for common status values
#       (no choices on model, so values are mapped from observed conventions;
#        unknown values fall back to a neutral grey pill)
#     - date_hierarchy on last_seen; ordering = ("-last_seen",)
#   FileStatusHistoryAdmin:
#     - status_badge + previous_status_badge: same color-coding
#     - date_hierarchy on timestamp; ordering = ("-timestamp",) (model Meta already sets this)
#   Media: loads shared admin/custom.css on all five classes

from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from relations.models import (
    FileStatus,
    FileStatusHistory,
    LogRelationship,
    Relation,
    TagRelationship,
)

# ---------------------------------------------------------------------------
# Status colour map — no model choices defined, so we enumerate common values.
# mark_safe is used below; bg/fg values are hardcoded here (not user input).
# ---------------------------------------------------------------------------
_STATUS_COLORS: dict[str, tuple[str, str]] = {
    "clean":       ("#dcfce7", "#166534"),
    "malicious":   ("#fee2e2", "#991b1b"),
    "suspicious":  ("#fef9c3", "#854d0e"),
    "unknown":     ("#f3f4f6", "#374151"),
    "whitelisted": ("#dbeafe", "#1e40af"),
    "quarantined": ("#fce7f3", "#9d174d"),
}
_STATUS_DEFAULT = ("#f3f4f6", "#374151")


def _status_badge(status: str):
    """Return a colour-coded pill span for a file status value."""
    bg, fg = _STATUS_COLORS.get(status.lower(), _STATUS_DEFAULT)
    # mark_safe is intentional: bg/fg are hardcoded constants; status is escaped by format_html.
    return format_html(
        '<span style="background:{};color:{};padding:2px 10px;'
        'border-radius:9999px;font-size:0.82em;font-weight:600;">{}</span>',
        bg,
        fg,
        status,
    )


# ---------------------------------------------------------------------------
# RelationAdmin
# ---------------------------------------------------------------------------

@admin.register(Relation)
class RelationAdmin(admin.ModelAdmin):
    list_display = (
        "source_type",
        "source_value_short",
        "target_type",
        "target_value_short",
        "pattern_type",
        "strength",
        "connection_count",
        "last_seen",
    )
    list_filter = ("source_type", "target_type", "pattern_type")
    search_fields = ("source_value", "target_value")
    readonly_fields = ("first_seen", "last_seen")
    date_hierarchy = "last_seen"
    ordering = ("-connection_count",)

    class Media:
        css = {"all": ("admin/custom.css",)}

    @admin.display(description="Source Value")
    def source_value_short(self, obj):
        v = obj.source_value
        return (v[:60] + "\u2026") if len(v) > 60 else v

    @admin.display(description="Target Value")
    def target_value_short(self, obj):
        v = obj.target_value
        return (v[:60] + "\u2026") if len(v) > 60 else v


# ---------------------------------------------------------------------------
# LogRelationshipAdmin
# ---------------------------------------------------------------------------

@admin.register(LogRelationship)
class LogRelationshipAdmin(admin.ModelAdmin):
    list_display = (
        "source_log_link",
        "target_log_link",
        "type",
        "relationship",
        "created_by",
        "created_at",
    )
    list_filter = ("type", "created_at")
    search_fields = ("relationship", "notes", "created_by")
    readonly_fields = ("created_at",)
    date_hierarchy = "created_at"
    ordering = ("-created_at",)

    class Media:
        css = {"all": ("admin/custom.css",)}

    @admin.display(description="Source Log", ordering="source_id")
    def source_log_link(self, obj):
        # source_id is an IntegerField (not FK) — link is best-effort; Log may not exist.
        url = reverse("admin:logs_log_change", args=[obj.source_id])
        return format_html('<a href="{}">Log\u00a0{}</a>', url, obj.source_id)

    @admin.display(description="Target Log", ordering="target_id")
    def target_log_link(self, obj):
        url = reverse("admin:logs_log_change", args=[obj.target_id])
        return format_html('<a href="{}">Log\u00a0{}</a>', url, obj.target_id)


# ---------------------------------------------------------------------------
# TagRelationshipAdmin
# ---------------------------------------------------------------------------

@admin.register(TagRelationship)
class TagRelationshipAdmin(admin.ModelAdmin):
    list_display = (
        "source_tag_id",
        "target_tag_id",
        "cooccurrence_count",
        "sequence_count",
        "correlation_strength",
        "last_seen",
    )
    list_filter = ("last_seen",)
    # source_tag_id / target_tag_id are IntegerFields; searching by numeric ID is
    # still useful when cross-referencing with the Tag admin list.
    search_fields = ("source_tag_id", "target_tag_id")
    readonly_fields = ("first_seen", "last_seen")
    date_hierarchy = "last_seen"
    ordering = ("-cooccurrence_count",)

    class Media:
        css = {"all": ("admin/custom.css",)}


# ---------------------------------------------------------------------------
# FileStatusAdmin
# ---------------------------------------------------------------------------

@admin.register(FileStatus)
class FileStatusAdmin(admin.ModelAdmin):
    list_display = (
        "filename",
        "hostname",
        "internal_ip",
        "status_badge",
        "hash_algorithm",
        "username",
        "analyst",
        "last_seen",
    )
    list_filter = ("status", "hostname", "hash_algorithm")
    search_fields = ("filename", "hostname", "username", "analyst", "hash_value")
    readonly_fields = ("first_seen", "last_seen")
    date_hierarchy = "last_seen"
    ordering = ("-last_seen",)

    class Media:
        css = {"all": ("admin/custom.css",)}

    @admin.display(description="Status", ordering="status")
    def status_badge(self, obj):
        if not obj.status:
            return "—"
        return _status_badge(obj.status)


# ---------------------------------------------------------------------------
# FileStatusHistoryAdmin
# ---------------------------------------------------------------------------

@admin.register(FileStatusHistory)
class FileStatusHistoryAdmin(admin.ModelAdmin):
    list_display = (
        "filename",
        "hostname",
        "previous_status_badge",
        "status_badge",
        "username",
        "analyst",
        "timestamp",
    )
    list_filter = ("status", "previous_status", "hostname")
    search_fields = ("filename", "hostname", "username", "analyst")
    readonly_fields = ("timestamp",)
    date_hierarchy = "timestamp"
    ordering = ("-timestamp",)

    class Media:
        css = {"all": ("admin/custom.css",)}

    @admin.display(description="Status", ordering="status")
    def status_badge(self, obj):
        if not obj.status:
            return "—"
        return _status_badge(obj.status)

    @admin.display(description="Previous Status", ordering="previous_status")
    def previous_status_badge(self, obj):
        if not obj.previous_status:
            return "—"
        return _status_badge(obj.previous_status)
