from django.contrib import admin
from operations.models import Operation, UserOperation


class UserOperationInline(admin.TabularInline):
    model = UserOperation
    extra = 0
    readonly_fields = ("assigned_at", "last_accessed")


@admin.register(Operation)
class OperationAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_by", "created_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("name", "description", "created_by")
    readonly_fields = ("created_at", "updated_at")
    inlines = [UserOperationInline]


@admin.register(UserOperation)
class UserOperationAdmin(admin.ModelAdmin):
    list_display = ("username", "operation", "is_primary",
                    "assigned_by", "assigned_at")
    list_filter = ("is_primary", "assigned_at")
    search_fields = ("username", "assigned_by")
    readonly_fields = ("assigned_at", "last_accessed")
