from django.contrib import admin
from api_keys.models import ApiKey


@admin.register(ApiKey)
class ApiKeyAdmin(admin.ModelAdmin):
    list_display = ("name", "key_id", "created_by", "is_active",
                    "created_at", "expires_at", "last_used")
    list_filter = ("is_active", "created_at", "expires_at")
    search_fields = ("name", "key_id", "created_by", "description")
    readonly_fields = ("key_id", "key_hash", "created_at",
                       "updated_at", "last_used")
