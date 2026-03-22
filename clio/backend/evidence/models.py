from django.db import models


class EvidenceFile(models.Model):
    """A file attached to a log entry as supporting evidence."""

    log = models.ForeignKey(
        "logs.Log",
        on_delete=models.CASCADE,
        related_name="evidence_files",
    )
    filename = models.CharField(max_length=255)
    original_filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=100, blank=True, default="")
    file_size = models.IntegerField()
    upload_date = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.CharField(max_length=100, blank=True, default="")
    description = models.TextField(blank=True, default="")
    md5_hash = models.CharField(max_length=32, blank=True, default="")
    filepath = models.CharField(max_length=255, blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "evidence_files"
        indexes = [
            models.Index(fields=["log"], name="idx_evidence_log"),
            models.Index(fields=["uploaded_by"], name="idx_evidence_uploader"),
        ]

    def __str__(self):
        return f"{self.original_filename} (Log {self.log_id})"
