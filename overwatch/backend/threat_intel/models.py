from django.db import models


class MitreTechnique(models.Model):
    """A single MITRE ATT&CK technique or sub-technique."""

    stix_id = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text="STIX object ID (e.g. attack-pattern--…)",
    )
    external_id = models.CharField(
        max_length=20,
        db_index=True,
        help_text="ATT&CK ID (e.g. T1059, T1059.001)",
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    domain = models.CharField(
        max_length=50,
        db_index=True,
        help_text="ATT&CK domain: enterprise-attack, mobile-attack, ics-attack",
    )
    # Stored as comma-separated strings for simplicity / searchability
    tactics = models.CharField(
        max_length=500,
        blank=True,
        default="",
        help_text="Comma-separated tactic phase names",
    )
    platforms = models.CharField(
        max_length=500,
        blank=True,
        default="",
        help_text="Comma-separated platform names",
    )
    ingested_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "threat_intel_mitre_technique"
        ordering = ["external_id"]
        verbose_name = "MITRE Technique"
        verbose_name_plural = "MITRE Techniques"
        indexes = [
            models.Index(fields=["domain", "external_id"],
                         name="idx_mitre_domain_extid"),
        ]

    def __str__(self):
        return f"{self.external_id} – {self.name}"


class NvdCve(models.Model):
    """A single NVD CVE entry."""

    cve_id = models.CharField(
        max_length=30,
        unique=True,
        db_index=True,
        help_text="CVE identifier (e.g. CVE-2023-12345)",
    )
    description = models.TextField(blank=True, default="")
    cvss_score = models.FloatField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Highest available CVSS base score (v3.1 → v3.0 → v2.0)",
    )
    published_date = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
    )
    # Stored as newline-separated CPE strings (up to 20 per ingest)
    affected_products = models.TextField(
        blank=True,
        default="",
        help_text="Newline-separated CPE match strings",
    )
    ingested_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "threat_intel_nvd_cve"
        ordering = ["-published_date", "cve_id"]
        verbose_name = "NVD CVE"
        verbose_name_plural = "NVD CVEs"

    def __str__(self):
        score = f" [{self.cvss_score}]" if self.cvss_score is not None else ""
        return f"{self.cve_id}{score}"


class ChatSession(models.Model):
    """
    Persistent named chat session linking a JWTUser to a django-ai-assistant Thread.

    Thread.created_by is always None for JWTUser (stateless, no Django model row),
    so we store the username ourselves.

    thread_id stores the integer PK of the django-ai-assistant Thread.  It is
    nullable to handle the rare case where Thread creation fails at session-create
    time; _handle_session_message will create the Thread on first send instead.

    BUG 1 FIX: Thread.id is a BigAutoField (integer), not UUID.  The previous
    UUIDField coerced integer PKs via uuid.UUID(int=N), producing strings like
    '00000000-0000-0000-0000-000000000001' that then failed the reverse lookup
    with "Field 'id' expected a number but got '…'".  Changed to BigIntegerField.
    """

    thread_id = models.BigIntegerField(
        unique=True,
        null=True,
        blank=True,
        help_text="django-ai-assistant Thread.id (integer PK) backing this session",
    )
    username = models.CharField(
        max_length=150,
        db_index=True,
        help_text="JWTUser.username who owns this session",
    )
    name = models.CharField(
        max_length=255,
        default="",
        blank=True,
        help_text="Display name; set from first 60 chars of first user message",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "threat_intel_chat_session"
        ordering = ["-updated_at"]
        verbose_name = "Chat Session"
        verbose_name_plural = "Chat Sessions"

    def __str__(self):
        return f"ChatSession({self.id}, {self.name!r}, user={self.username})"


class SessionSource(models.Model):
    """
    Records which RAG source records were retrieved during a session's lifetime.

    One row per (session, source_type, record_id) triple.  Populated by the
    Celery chat task after each assistant reply by scanning the reply text for
    CVE IDs and ATT&CK technique IDs.

    BUG 2 FIX: enables GET /api/chat/sessions/{id}/sources/ to return per-session
                counts so the RAG panel can show "used in this session" vs
                "total indexed".
    BUG 3 FIX: source_url is populated for MITRE and NVD records so future
                citation UI can link directly to authoritative sources.
    """

    SOURCE_MITRE = "mitre"
    SOURCE_NVD = "nvd"
    SOURCE_DB = "db"
    SOURCE_TYPE_CHOICES = [
        (SOURCE_MITRE, "MITRE ATT&CK"),
        (SOURCE_NVD, "NVD CVE"),
        (SOURCE_DB, "Django DB"),
    ]

    session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name="sources",
        db_index=True,
    )
    source_type = models.CharField(
        max_length=10,
        choices=SOURCE_TYPE_CHOICES,
        db_index=True,
    )
    record_id = models.CharField(
        max_length=100,
        help_text="e.g. T1059, CVE-2023-12345, or model name for DB sources",
    )
    source_url = models.URLField(
        max_length=500,
        null=True,
        blank=True,
        help_text=(
            "Authoritative URL for this record. "
            "MITRE: https://attack.mitre.org/techniques/{id}/  "
            "NVD: https://nvd.nist.gov/vuln/detail/{id}  "
            "DB: null (no canonical URL)"
        ),
    )
    retrieved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "threat_intel_session_source"
        unique_together = [("session", "source_type", "record_id")]
        ordering = ["retrieved_at"]
        verbose_name = "Session Source"
        verbose_name_plural = "Session Sources"

    def __str__(self):
        return f"{self.source_type}:{self.record_id} (session {self.session_id})"
