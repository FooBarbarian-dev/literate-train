from django.conf import settings
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

class LogAIContext(models.Model):
    log_entry = models.OneToOneField(
        'Log',
        on_delete=models.CASCADE,
        related_name='ai_context'
    )
    generated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(
        max_length=20,
        choices=[('pending', 'pending'), ('complete', 'complete'), ('error', 'error')],
        default='pending'
    )
    mitre_techniques = models.JSONField(default=list)
    cves = models.JSONField(default=list)
    summary = models.TextField(blank=True)
    error_message = models.TextField(blank=True)
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, on_delete=models.SET_NULL
    )

class LogAIContextSource(models.Model):
    ai_context = models.ForeignKey(
        LogAIContext, on_delete=models.CASCADE, related_name='sources'
    )
    source_type = models.CharField(max_length=20)
    record_id = models.CharField(max_length=100)
    source_url = models.URLField(blank=True)
    retrieved_at = models.DateTimeField(auto_now_add=True)
