from django.contrib import admin
from templates_mgmt.models import LogTemplate


@admin.register(LogTemplate)
class LogTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "created_by", "created_at", "updated_at")
    search_fields = ("name", "created_by")
    readonly_fields = ("created_at", "updated_at")
