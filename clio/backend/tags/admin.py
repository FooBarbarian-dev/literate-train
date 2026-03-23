from django.contrib import admin
from tags.models import Tag, LogTag


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "color", "category", "is_default",
                    "created_by", "created_at")
    list_filter = ("category", "is_default", "created_at")
    search_fields = ("name", "description", "created_by")
    readonly_fields = ("created_at", "updated_at")


@admin.register(LogTag)
class LogTagAdmin(admin.ModelAdmin):
    list_display = ("log", "tag", "tagged_by", "tagged_at")
    list_filter = ("tagged_at",)
    search_fields = ("tagged_by",)
    readonly_fields = ("tagged_at",)
    raw_id_fields = ("log", "tag")
