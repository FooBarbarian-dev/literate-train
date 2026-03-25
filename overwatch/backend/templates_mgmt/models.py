from django.db import models


class LogTemplate(models.Model):
    """Reusable template for pre-populating log entry fields."""

    name = models.CharField(max_length=100)
    template_data = models.JSONField(default=dict, blank=True)
    created_by = models.CharField(max_length=100, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "log_templates"

    def __str__(self):
        return self.name
