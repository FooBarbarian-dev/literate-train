from django.contrib import admin
from logs.models import Log


@admin.register(Log)
class LogAdmin(admin.ModelAdmin):
    list_display = ("id", "timestamp", "hostname", "username", "analyst",
                    "command_preview", "locked", "created_at")
    list_filter = ("locked", "analyst", "timestamp")
    search_fields = ("hostname", "username", "command", "notes",
                     "domain", "filename")
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "timestamp"

    @admin.display(description="Command")
    def command_preview(self, obj):
        return obj.command[:80] + "\u2026" if len(obj.command) > 80 else obj.command
