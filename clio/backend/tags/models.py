from django.db import models
from django.db.models.functions import Lower


class Tag(models.Model):
    """Categorization tag that can be applied to log entries."""

    name = models.CharField(max_length=50, unique=True)
    color = models.CharField(max_length=7, default="#6B7280")
    category = models.CharField(max_length=50, blank=True, default="")
    description = models.TextField(blank=True, default="")
    is_default = models.BooleanField(default=False)
    created_by = models.CharField(max_length=100, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tags"
        indexes = [
            models.Index(Lower("name"), name="idx_tags_name_lower"),
            models.Index(fields=["category"], name="idx_tags_category"),
            models.Index(fields=["is_default"], name="idx_tags_is_default"),
        ]

    def save(self, *args, **kwargs):
        self.name = self.name.strip().lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class LogTag(models.Model):
    """Through-table linking logs to tags."""

    log = models.ForeignKey(
        "logs.Log",
        on_delete=models.CASCADE,
        related_name="log_tags",
    )
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        related_name="log_tags",
    )
    tagged_by = models.CharField(max_length=100, blank=True, default="")
    tagged_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "log_tags"
        unique_together = [("log", "tag")]
        indexes = [
            models.Index(fields=["log"], name="idx_logtag_log"),
            models.Index(fields=["tag"], name="idx_logtag_tag"),
            models.Index(fields=["tagged_at"], name="idx_logtag_tagged_at"),
        ]

    def __str__(self):
        return f"{self.log_id} -> {self.tag}"
