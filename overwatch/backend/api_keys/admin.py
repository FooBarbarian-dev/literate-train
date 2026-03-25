# UX Audit 2026-03-23 — Changes:
#   - operation added to list_display; list_select_related eliminates N+1 on FK
#   - autocomplete_fields = ("operation",) — OperationAdmin already defines search_fields
#   - pretty_permissions / pretty_metadata: JSONField rendered as scrollable <pre> block
#   - date_hierarchy on created_at for drill-down navigation
#   - fieldsets: Key Identity / Permissions & Scope / Status / Metadata / Audit
#   - ordering = ("-created_at",) — newest keys surfaced first
#   - Media: loads shared admin/custom.css (monospace + JSON pretty-print styles)

import json

from django.contrib import admin
from django.utils.safestring import mark_safe

from api_keys.models import ApiKey


@admin.register(ApiKey)
class ApiKeyAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "key_id",
        "operation",
        "created_by",
        "is_active",
        "created_at",
        "expires_at",
        "last_used",
    )
    list_filter = ("is_active", "created_at", "expires_at")
    search_fields = ("name", "key_id", "created_by", "description")
    readonly_fields = (
        "key_id",
        "key_hash",
        "created_at",
        "updated_at",
        "last_used",
        "pretty_permissions",
        "pretty_metadata",
    )
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    list_select_related = ("operation",)
    autocomplete_fields = ("operation",)

    fieldsets = (
        (
            "Key Identity",
            {
                "fields": ("name", "key_id", "key_hash", "description"),
            },
        ),
        (
            "Permissions & Scope",
            {
                "fields": ("operation", "permissions", "pretty_permissions"),
            },
        ),
        (
            "Status",
            {
                "fields": ("is_active", "expires_at", "last_used"),
            },
        ),
        (
            "Metadata",
            {
                "fields": ("pretty_metadata",),
                "classes": ("collapse",),
            },
        ),
        (
            "Audit",
            {
                "fields": ("created_by", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    class Media:
        css = {"all": ("admin/custom.css",)}

    @admin.display(description="Permissions (preview)")
    def pretty_permissions(self, obj):
        # mark_safe is intentional: json.dumps output contains no user-controlled HTML.
        return mark_safe(
            f'<pre class="json-pretty">{json.dumps(obj.permissions, indent=2)}</pre>'
        )

    @admin.display(description="Metadata (preview)")
    def pretty_metadata(self, obj):
        if not obj.metadata:
            return "—"
        return mark_safe(
            f'<pre class="json-pretty">{json.dumps(obj.metadata, indent=2)}</pre>'
        )
