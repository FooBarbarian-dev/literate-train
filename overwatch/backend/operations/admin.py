# UX Audit 2026-03-23 — Changes:
#   OperationAdmin:
#     - tag added to list_display so the associated tag is visible at a glance
#     - list_select_related = ("tag",): eliminates N+1 on tag FK in list view
#     - autocomplete_fields = ("tag",): replaces slow full-queryset select widget
#       (TagAdmin defines search_fields, so autocomplete is supported)
#     - date_hierarchy on created_at for drill-down navigation
#     - ordering = ("name",): alphabetical list is easiest to scan
#   UserOperationAdmin:
#     - list_select_related = ("operation",): eliminates N+1 on operation FK
#     - autocomplete_fields = ("operation",): replaces slow full-queryset select
#       (OperationAdmin defines search_fields above)
#     - search_fields gains operation__name traversal
#     - ordering = ("username", "operation__name"): predictable sort
#   Media: loads shared admin/custom.css

from django.contrib import admin

from operations.models import Operation, UserOperation


class UserOperationInline(admin.TabularInline):
    model = UserOperation
    extra = 0
    readonly_fields = ("assigned_at", "last_accessed")


@admin.register(Operation)
class OperationAdmin(admin.ModelAdmin):
    list_display = ("name", "tag", "is_active", "created_by", "created_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("name", "description", "created_by")
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "created_at"
    ordering = ("name",)
    list_select_related = ("tag",)
    autocomplete_fields = ("tag",)
    inlines = [UserOperationInline]

    class Media:
        css = {"all": ("admin/custom.css",)}


@admin.register(UserOperation)
class UserOperationAdmin(admin.ModelAdmin):
    list_display = (
        "username",
        "operation",
        "is_primary",
        "assigned_by",
        "assigned_at",
    )
    list_filter = ("is_primary", "assigned_at")
    search_fields = ("username", "assigned_by", "operation__name")
    readonly_fields = ("assigned_at", "last_accessed")
    ordering = ("username", "operation__name")
    list_select_related = ("operation",)
    autocomplete_fields = ("operation",)

    class Media:
        css = {"all": ("admin/custom.css",)}
