# UX Audit 2026-03-23 — Changes:
#   - list_filter = ("created_by", "created_at"): was completely missing
#   - pretty_template_data: template_data JSONField rendered as scrollable <pre> block
#     instead of a collapsed one-liner
#   - date_hierarchy on created_at for drill-down navigation
#   - ordering = ("name",): alphabetical sort is most natural for a template library
#   - fieldsets: Template / Data / Audit
#   - Media: loads shared admin/custom.css

import json

from django.contrib import admin
from django.utils.safestring import mark_safe

from templates_mgmt.models import LogTemplate


@admin.register(LogTemplate)
class LogTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "created_by", "created_at", "updated_at")
    list_filter = ("created_by", "created_at")
    search_fields = ("name", "created_by")
    readonly_fields = ("created_at", "updated_at", "pretty_template_data")
    date_hierarchy = "created_at"
    ordering = ("name",)

    fieldsets = (
        (
            "Template",
            {
                "fields": ("name", "created_by"),
            },
        ),
        (
            "Data",
            {
                "fields": ("template_data", "pretty_template_data"),
            },
        ),
        (
            "Audit",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    class Media:
        css = {"all": ("admin/custom.css",)}

    @admin.display(description="Template Data (preview)")
    def pretty_template_data(self, obj):
        if not obj.template_data:
            return "—"
        # mark_safe is intentional: json.dumps output contains no user-controlled HTML.
        return mark_safe(
            f'<pre class="json-pretty">{json.dumps(obj.template_data, indent=2)}</pre>'
        )
