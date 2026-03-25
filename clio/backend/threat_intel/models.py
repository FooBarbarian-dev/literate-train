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
