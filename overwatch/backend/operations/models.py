from django.db import models


class Operation(models.Model):
    """An operational grouping that scopes log entries and user access."""

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, default="")
    tag = models.ForeignKey(
        "tags.Tag",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column="tag_id",
        related_name="operations",
    )
    is_active = models.BooleanField(default=True)
    created_by = models.CharField(max_length=100, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "operations"
        indexes = [
            models.Index(fields=["tag"], name="idx_ops_tag"),
            models.Index(fields=["is_active"], name="idx_ops_is_active"),
        ]

    def __str__(self):
        return self.name


class UserOperation(models.Model):
    """Maps a username to an operation, controlling access scope."""

    username = models.CharField(max_length=100)
    operation = models.ForeignKey(
        Operation,
        on_delete=models.CASCADE,
        db_column="operation_id",
        related_name="user_operations",
    )
    is_primary = models.BooleanField(default=False)
    assigned_by = models.CharField(max_length=100, blank=True, default="")
    assigned_at = models.DateTimeField(auto_now_add=True)
    last_accessed = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_operations"
        constraints = [
            models.UniqueConstraint(
                fields=["username", "operation"],
                name="uq_useroperation_username_operation",
            ),
        ]
        indexes = [
            models.Index(fields=["username"], name="idx_userop_username"),
            models.Index(fields=["operation"], name="idx_userop_op"),
        ]

    def __str__(self):
        return f"{self.username} -> {self.operation}"
