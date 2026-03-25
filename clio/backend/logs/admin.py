# UX Audit 2026-03-23 — Changes:
#   - BUG FIX: operation_display used str.join() over format_html() generators;
#     str.join() returns plain str, stripping SafeString — HTML was rendered escaped.
#     Replaced with format_html_join() which preserves SafeString across the join.
#   - fieldsets on the change/add view: groups 20 fields into 6 logical sections
#     (Identity / Network / Activity / File Hash / Security / Audit)
#   - locked_by added to readonly_fields (auto-managed, should not be hand-edited)
#   - list_per_page = 50: log tables can grow very large; 100 was too heavy
#   - show_full_result_count = False: suppresses expensive COUNT(*) on filtered lists
#   - Media: loads shared admin/custom.css (monospace command/hash, secrets warning)

from django.contrib import admin
from django.utils.html import format_html_join

from logs.models import Log
from tags.models import LogTag


class LogTagInline(admin.TabularInline):
    model = LogTag
    extra = 0
    readonly_fields = ("tagged_at",)
    autocomplete_fields = ("tag",)


@admin.register(Log)
class LogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "timestamp",
        "hostname",
        "username",
        "analyst",
        "command_preview",
        "operation_display",
        "locked",
        "created_at",
    )
    list_filter = ("locked", "analyst", "timestamp")
    search_fields = (
        "hostname",
        "username",
        "command",
        "notes",
        "domain",
        "filename",
    )
    readonly_fields = ("created_at", "updated_at", "locked_by")
    date_hierarchy = "timestamp"
    list_per_page = 50
    show_full_result_count = False
    inlines = [LogTagInline]

    fieldsets = (
        (
            "Identity",
            {
                "fields": ("timestamp", "analyst", "hostname", "domain", "username"),
            },
        ),
        (
            "Network",
            {
                "fields": ("internal_ip", "external_ip", "mac_address"),
                "classes": ("collapse",),
            },
        ),
        (
            "Activity",
            {
                "fields": ("command", "filename", "pid", "status"),
            },
        ),
        (
            "File Hash",
            {
                "fields": ("hash_algorithm", "hash_value"),
                "classes": ("collapse",),
            },
        ),
        (
            "Security",
            {
                "description": "Handle secrets with care — visible to all admin users.",
                "fields": ("notes", "secrets", "locked", "locked_by"),
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

    @admin.display(description="Command")
    def command_preview(self, obj):
        return obj.command[:80] + "\u2026" if len(obj.command) > 80 else obj.command

    @admin.display(description="Operation")
    def operation_display(self, obj):
        op_tags = [
            lt.tag
            for lt in obj.log_tags.all()
            if lt.tag.category == "operation"
        ]
        if not op_tags:
            return "—"
        # format_html_join preserves SafeString status across the join;
        # plain str.join() would strip it and cause the HTML to be escaped.
        return format_html_join(
            ", ",
            '<span style="color:{};font-weight:600;">{}</span>',
            ((tag.color or "#3B82F6", tag.name) for tag in op_tags),
        )

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("log_tags__tag")
