# UX Audit 2026-03-23 — Changes:
#   - file_size_display: bytes → human-readable KB/MB (raw integer was unreadable)
#   - log_link: FK rendered as clickable link to the Log change page instead of raw ID
#   - list_select_related = ("log",): eliminates N+1 query on log FK in list view
#   - date_hierarchy on upload_date for drill-down navigation
#   - pretty_metadata: JSONField rendered as scrollable <pre> block
#   - ordering = ("-upload_date",): newest evidence surfaced first
#   - fieldsets: File Info / Storage & Integrity / Upload / Metadata
#   - Media: loads shared admin/custom.css

import json

from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from evidence.models import EvidenceFile


def _human_size(size_bytes: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if size_bytes < 1024:
            return f"{size_bytes:.1f}\u00a0{unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f}\u00a0TB"


@admin.register(EvidenceFile)
class EvidenceFileAdmin(admin.ModelAdmin):
    list_display = (
        "original_filename",
        "log_link",
        "file_type",
        "file_size_display",
        "uploaded_by",
        "upload_date",
    )
    list_filter = ("file_type", "upload_date")
    search_fields = ("original_filename", "uploaded_by", "description")
    readonly_fields = (
        "upload_date",
        "md5_hash",
        "filepath",
        "filename",
        "file_size_display",
        "log_link",
        "pretty_metadata",
    )
    raw_id_fields = ("log",)
    date_hierarchy = "upload_date"
    ordering = ("-upload_date",)
    list_select_related = ("log",)

    fieldsets = (
        (
            "File Info",
            {
                "fields": (
                    "log_link",
                    "log",
                    "original_filename",
                    "filename",
                    "file_type",
                    "file_size_display",
                ),
            },
        ),
        (
            "Storage & Integrity",
            {
                "fields": ("filepath", "file", "md5_hash"),
            },
        ),
        (
            "Upload",
            {
                "fields": ("uploaded_by", "description", "upload_date"),
            },
        ),
        (
            "Metadata",
            {
                "fields": ("pretty_metadata",),
                "classes": ("collapse",),
            },
        ),
    )

    class Media:
        css = {"all": ("admin/custom.css",)}

    @admin.display(description="File Size", ordering="file_size")
    def file_size_display(self, obj):
        return _human_size(obj.file_size)

    @admin.display(description="Log", ordering="log_id")
    def log_link(self, obj):
        # mark_safe via format_html; URL comes from Django's own reverse(), not user data.
        url = reverse("admin:logs_log_change", args=[obj.log_id])
        return format_html('<a href="{}">{}</a>', url, str(obj.log))

    @admin.display(description="Metadata (preview)")
    def pretty_metadata(self, obj):
        if not obj.metadata:
            return "—"
        return mark_safe(
            f'<pre class="json-pretty">{json.dumps(obj.metadata, indent=2)}</pre>'
        )
