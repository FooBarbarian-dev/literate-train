from django.contrib import admin
from django.utils.html import format_html

from logs.models import Log
from tags.models import LogTag


class LogTagInline(admin.TabularInline):
    model = LogTag
    extra = 0
    readonly_fields = ("tagged_at",)
    autocomplete_fields = ("tag",)


@admin.register(Log)
class LogAdmin(admin.ModelAdmin):
    list_display = ("id", "timestamp", "hostname", "username", "analyst",
                    "command_preview", "operation_display", "locked", "created_at")
    list_filter = ("locked", "analyst", "timestamp")
    search_fields = ("hostname", "username", "command", "notes",
                     "domain", "filename")
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "timestamp"
    inlines = [LogTagInline]

    @admin.display(description="Command")
    def command_preview(self, obj):
        return obj.command[:80] + "\u2026" if len(obj.command) > 80 else obj.command

    @admin.display(description="Operation")
    def operation_display(self, obj):
        op_tags = [
            lt.tag for lt in obj.log_tags.select_related("tag").all()
            if lt.tag.category == "operation"
        ]
        if not op_tags:
            return "-"
        return ", ".join(
            format_html(
                '<span style="color: {};">{}</span>',
                tag.color or "#3B82F6",
                tag.name,
            )
            for tag in op_tags
        )

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("log_tags__tag")
