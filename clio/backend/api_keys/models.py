from django.db import models


def default_permissions():
    return ["logs:write"]


class ApiKey(models.Model):
    """API key for programmatic access to the Clio platform."""

    name = models.CharField(max_length=100)
    key_id = models.CharField(max_length=50, unique=True)
    key_hash = models.CharField(max_length=255)
    created_by = models.CharField(max_length=100, blank=True, default="")
    permissions = models.JSONField(default=default_permissions)
    description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    last_used = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    operation = models.ForeignKey(
        "operations.Operation",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="api_keys",
    )

    class Meta:
        db_table = "api_keys"
        indexes = [
            models.Index(fields=["key_id"], name="idx_apikey_key_id"),
            models.Index(fields=["created_by"], name="idx_apikey_created_by"),
            models.Index(fields=["is_active"], name="idx_apikey_is_active"),
            models.Index(fields=["operation"], name="idx_apikey_operation"),
        ]

    def __str__(self):
        return f"{self.name} ({self.key_id})"
