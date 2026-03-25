# UX Audit 2026-03-23 — Changes:
#   TagAdmin:
#     - color_swatch: renders the hex code as an inline colour swatch + <code> label
#       instead of a raw "#6B7280" string — immediately scannable
#     - color_swatch added to readonly_fields so it appears on the change page too
#   LogTagAdmin:
#     - list_select_related = ("log", "tag"): both FKs shown in list_display; was N+2
#     - date_hierarchy on tagged_at for drill-down navigation
#     - search_fields gains tag__name and log__hostname traversals
#   Media: loads shared admin/custom.css

from django.contrib import admin
from django.utils.html import format_html

from tags.models import LogTag, Tag


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "color_swatch",
        "category",
        "is_default",
        "created_by",
        "created_at",
    )
    list_filter = ("category", "is_default", "created_at")
    search_fields = ("name", "description", "created_by")
    readonly_fields = ("created_at", "updated_at", "color_swatch")

    class Media:
        css = {"all": ("admin/custom.css",)}

    @admin.display(description="Color")
    def color_swatch(self, obj):
        # format_html escapes obj.color; the inline style value is the hex string itself.
        return format_html(
            '<span style="display:inline-block;width:16px;height:16px;'
            "border-radius:3px;background:{};border:1px solid #d1d5db;"
            'vertical-align:middle;margin-right:6px;"></span>'
            "<code>{}</code>",
            obj.color,
            obj.color,
        )


@admin.register(LogTag)
class LogTagAdmin(admin.ModelAdmin):
    list_display = ("log", "tag", "tagged_by", "tagged_at")
    list_filter = ("tagged_at",)
    search_fields = ("tagged_by", "tag__name", "log__hostname")
    readonly_fields = ("tagged_at",)
    raw_id_fields = ("log", "tag")
    date_hierarchy = "tagged_at"
    list_select_related = ("log", "tag")

    class Media:
        css = {"all": ("admin/custom.css",)}
