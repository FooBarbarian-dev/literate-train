from django.contrib.postgres.fields import ArrayField
from django.db import models


class Relation(models.Model):
    """Tracks relationships between entities discovered through log analysis."""

    SOURCE_TYPE_CHOICES = [
        ("hostname", "Hostname"),
        ("ip", "IP"),
        ("domain", "Domain"),
        ("username", "Username"),
    ]

    TARGET_TYPE_CHOICES = [
        ("hostname", "Hostname"),
        ("ip", "IP"),
        ("domain", "Domain"),
        ("command", "Command"),
    ]

    RELATIONSHIP_TYPE_CHOICES = [
        ("host", "Host"),
        ("ip", "IP"),
        ("domain", "Domain"),
        ("user_command", "User Command"),
    ]

    source_type = models.CharField(max_length=20, choices=SOURCE_TYPE_CHOICES)
    source_value = models.CharField(max_length=255)
    target_type = models.CharField(max_length=20, choices=TARGET_TYPE_CHOICES)
    target_value = models.CharField(max_length=255)

    relationship_type = models.CharField(
        max_length=30,
        choices=RELATIONSHIP_TYPE_CHOICES,
    )

    strength = models.PositiveIntegerField(default=1)
    connection_count = models.PositiveIntegerField(default=1)

    first_seen = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)

    operation_tags = ArrayField(
        models.CharField(max_length=255),
        default=list,
        blank=True,
    )
    source_log_ids = ArrayField(
        models.IntegerField(),
        default=list,
        blank=True,
    )
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "relations"
        constraints = [
            models.UniqueConstraint(
                fields=["source_type", "source_value", "target_type", "target_value"],
                name="uq_relation_source_target",
            ),
        ]
        indexes = [
            models.Index(fields=["source_type"], name="idx_rel_source_type"),
            models.Index(fields=["target_type"], name="idx_rel_target_type"),
            models.Index(fields=["relationship_type"], name="idx_rel_rel_type"),
        ]

    def __str__(self):
        return f"{self.source_type}:{self.source_value} -> {self.target_type}:{self.target_value}"


class FileStatus(models.Model):
    """Tracks current status of files across hosts."""

    filename = models.CharField(max_length=254)
    status = models.CharField(max_length=50, blank=True, default="")
    hash_algorithm = models.CharField(max_length=50, blank=True, default="")
    hash_value = models.CharField(max_length=128, blank=True, default="")

    hostname = models.CharField(max_length=75, blank=True, default="")
    internal_ip = models.CharField(max_length=45, blank=True, default="")
    external_ip = models.CharField(max_length=45, blank=True, default="")
    mac_address = models.CharField(max_length=17, blank=True, default="")

    username = models.CharField(max_length=75, blank=True, default="")
    analyst = models.CharField(max_length=100, blank=True, default="")
    notes = models.TextField(blank=True, default="")
    command = models.TextField(blank=True, default="")
    secrets = models.TextField(blank=True, default="")

    first_seen = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)

    metadata = models.JSONField(default=dict, blank=True)

    operation_tags = ArrayField(
        models.IntegerField(),
        default=list,
        blank=True,
    )
    source_log_ids = ArrayField(
        models.IntegerField(),
        default=list,
        blank=True,
    )

    class Meta:
        db_table = "file_status"
        constraints = [
            models.UniqueConstraint(
                fields=["filename", "hostname", "internal_ip"],
                name="uq_file_status_file_host_ip",
            ),
        ]
        indexes = [
            models.Index(fields=["filename"], name="idx_fs_filename"),
            models.Index(fields=["hostname"], name="idx_fs_hostname"),
            models.Index(fields=["status"], name="idx_fs_status"),
            models.Index(fields=["hash_value"], name="idx_fs_hash_value"),
        ]

    def __str__(self):
        return f"{self.filename} on {self.hostname} ({self.status})"


class FileStatusHistory(models.Model):
    """Historical record of file status changes."""

    filename = models.CharField(max_length=254)
    status = models.CharField(max_length=50, blank=True, default="")
    previous_status = models.CharField(max_length=50, blank=True, default="")

    hash_algorithm = models.CharField(max_length=50, blank=True, default="")
    hash_value = models.CharField(max_length=128, blank=True, default="")

    hostname = models.CharField(max_length=75, blank=True, default="")
    internal_ip = models.CharField(max_length=45, blank=True, default="")
    external_ip = models.CharField(max_length=45, blank=True, default="")
    mac_address = models.CharField(max_length=17, blank=True, default="")

    username = models.CharField(max_length=75, blank=True, default="")
    analyst = models.CharField(max_length=100, blank=True, default="")
    notes = models.TextField(blank=True, default="")
    command = models.TextField(blank=True, default="")
    secrets = models.TextField(blank=True, default="")

    timestamp = models.DateTimeField(auto_now_add=True)

    metadata = models.JSONField(default=dict, blank=True)

    operation_tags = ArrayField(
        models.IntegerField(),
        default=list,
        blank=True,
    )
    source_log_ids = ArrayField(
        models.IntegerField(),
        default=list,
        blank=True,
    )

    class Meta:
        db_table = "file_status_history"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["filename"], name="idx_fsh_filename"),
            models.Index(fields=["-timestamp"], name="idx_fsh_timestamp"),
            models.Index(fields=["hostname"], name="idx_fsh_hostname"),
        ]

    def __str__(self):
        return f"{self.filename} [{self.previous_status} -> {self.status}] at {self.timestamp}"


class LogRelationship(models.Model):
    """Tracks relationships between log entries."""

    TYPE_CHOICES = [
        ("parent_child", "Parent-Child"),
        ("linked", "Linked"),
        ("dependency", "Dependency"),
        ("correlation", "Correlation"),
    ]

    source_id = models.IntegerField(db_index=True)
    target_id = models.IntegerField(db_index=True)

    type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    relationship = models.CharField(max_length=100, blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=100, blank=True, default="")
    notes = models.TextField(blank=True, default="")

    class Meta:
        db_table = "log_relationships"
        indexes = [
            models.Index(fields=["source_id", "target_id"], name="idx_lr_src_tgt"),
            models.Index(fields=["type"], name="idx_lr_type"),
        ]

    def __str__(self):
        return f"Log {self.source_id} -{self.type}-> Log {self.target_id}"


class TagRelationship(models.Model):
    """Tracks relationships and co-occurrence patterns between tags."""

    source_tag_id = models.IntegerField(db_index=True)
    target_tag_id = models.IntegerField(db_index=True)

    cooccurrence_count = models.IntegerField(default=1)
    sequence_count = models.IntegerField(default=0)
    correlation_strength = models.FloatField(default=0.0)

    first_seen = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)

    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "tag_relationships"
        indexes = [
            models.Index(
                fields=["source_tag_id", "target_tag_id"],
                name="idx_tr_src_tgt",
            ),
            models.Index(fields=["correlation_strength"], name="idx_tr_corr"),
        ]

    def __str__(self):
        return f"Tag {self.source_tag_id} <-> Tag {self.target_tag_id} (strength={self.correlation_strength})"
