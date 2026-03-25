import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("logs", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="EvidenceFile",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "log",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="evidence_files",
                        to="logs.log",
                    ),
                ),
                ("filename", models.CharField(max_length=255)),
                ("original_filename", models.CharField(max_length=255)),
                (
                    "file_type",
                    models.CharField(blank=True, default="", max_length=100),
                ),
                ("file_size", models.IntegerField()),
                ("upload_date", models.DateTimeField(auto_now_add=True)),
                (
                    "uploaded_by",
                    models.CharField(blank=True, default="", max_length=100),
                ),
                ("description", models.TextField(blank=True, default="")),
                (
                    "md5_hash",
                    models.CharField(blank=True, default="", max_length=32),
                ),
                (
                    "filepath",
                    models.CharField(blank=True, default="", max_length=255),
                ),
                (
                    "metadata",
                    models.JSONField(blank=True, default=dict),
                ),
            ],
            options={
                "db_table": "evidence_files",
            },
        ),
        migrations.AddIndex(
            model_name="evidencefile",
            index=models.Index(
                fields=["log"], name="idx_evidence_log"
            ),
        ),
        migrations.AddIndex(
            model_name="evidencefile",
            index=models.Index(
                fields=["uploaded_by"], name="idx_evidence_uploader"
            ),
        ),
    ]
