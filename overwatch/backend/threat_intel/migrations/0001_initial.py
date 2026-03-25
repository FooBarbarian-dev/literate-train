from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="MitreTechnique",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "stix_id",
                    models.CharField(
                        db_index=True,
                        help_text="STIX object ID (e.g. attack-pattern--…)",
                        max_length=100,
                        unique=True,
                    ),
                ),
                (
                    "external_id",
                    models.CharField(
                        db_index=True,
                        help_text="ATT&CK ID (e.g. T1059, T1059.001)",
                        max_length=20,
                    ),
                ),
                ("name", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True, default="")),
                (
                    "domain",
                    models.CharField(
                        db_index=True,
                        help_text="ATT&CK domain: enterprise-attack, mobile-attack, ics-attack",
                        max_length=50,
                    ),
                ),
                (
                    "tactics",
                    models.CharField(
                        blank=True,
                        default="",
                        help_text="Comma-separated tactic phase names",
                        max_length=500,
                    ),
                ),
                (
                    "platforms",
                    models.CharField(
                        blank=True,
                        default="",
                        help_text="Comma-separated platform names",
                        max_length=500,
                    ),
                ),
                ("ingested_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "MITRE Technique",
                "verbose_name_plural": "MITRE Techniques",
                "db_table": "threat_intel_mitre_technique",
                "ordering": ["external_id"],
            },
        ),
        migrations.CreateModel(
            name="NvdCve",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "cve_id",
                    models.CharField(
                        db_index=True,
                        help_text="CVE identifier (e.g. CVE-2023-12345)",
                        max_length=30,
                        unique=True,
                    ),
                ),
                ("description", models.TextField(blank=True, default="")),
                (
                    "cvss_score",
                    models.FloatField(
                        blank=True,
                        db_index=True,
                        help_text="Highest available CVSS base score (v3.1 → v3.0 → v2.0)",
                        null=True,
                    ),
                ),
                (
                    "published_date",
                    models.DateTimeField(blank=True, db_index=True, null=True),
                ),
                (
                    "affected_products",
                    models.TextField(
                        blank=True,
                        default="",
                        help_text="Newline-separated CPE match strings",
                    ),
                ),
                ("ingested_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "NVD CVE",
                "verbose_name_plural": "NVD CVEs",
                "db_table": "threat_intel_nvd_cve",
                "ordering": ["-published_date", "cve_id"],
            },
        ),
        migrations.AddIndex(
            model_name="mitretechnique",
            index=models.Index(
                fields=["domain", "external_id"],
                name="idx_mitre_domain_extid",
            ),
        ),
    ]
