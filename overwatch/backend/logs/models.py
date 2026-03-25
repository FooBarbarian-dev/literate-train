from django.core.validators import MaxLengthValidator
from django.db import models
from django.db.models.functions import Lower


class Log(models.Model):
    """Core log entry model per spec 2.1.1."""

    timestamp = models.DateTimeField(db_index=True)
    internal_ip = models.CharField(max_length=45, blank=True, default="")
    external_ip = models.CharField(max_length=45, blank=True, default="")
    mac_address = models.CharField(max_length=17, blank=True, default="", db_index=True)
    hostname = models.CharField(max_length=75, blank=True, default="", db_index=True)
    domain = models.CharField(max_length=75, blank=True, default="")
    username = models.CharField(max_length=75, blank=True, default="")
    command = models.TextField(
        blank=True,
        default="",
        validators=[MaxLengthValidator(254)],
    )
    notes = models.TextField(
        blank=True,
        default="",
        validators=[MaxLengthValidator(254)],
    )
    filename = models.CharField(max_length=254, blank=True, default="")
    status = models.CharField(max_length=75, blank=True, default="")
    secrets = models.TextField(
        blank=True,
        default="",
        validators=[MaxLengthValidator(254)],
    )
    hash_algorithm = models.CharField(max_length=50, blank=True, default="")
    hash_value = models.CharField(max_length=128, blank=True, default="", db_index=True)
    pid = models.CharField(max_length=20, blank=True, default="")
    analyst = models.CharField(max_length=100, blank=True, default="", db_index=True)
    locked = models.BooleanField(default=False)
    locked_by = models.CharField(max_length=100, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    tags = models.ManyToManyField(
        "tags.Tag",
        through="tags.LogTag",
        related_name="logs",
        blank=True,
    )

    class Meta:
        db_table = "logs"
        ordering = ["-timestamp", "-id"]
        indexes = [
            models.Index(fields=["-timestamp", "-id"], name="idx_logs_ts_id"),
            models.Index(fields=["hostname", "timestamp"], name="idx_logs_host_ts"),
            models.Index(fields=["analyst", "timestamp"], name="idx_logs_analyst_ts"),
            models.Index(
                Lower("hash_value"),
                name="idx_logs_hash_lower",
            ),
        ]

    def __str__(self):
        return f"Log {self.id} [{self.timestamp}]"
