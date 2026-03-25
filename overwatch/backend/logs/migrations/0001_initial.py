import django.core.validators
import django.db.models.functions
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Log",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                ("timestamp", models.DateTimeField(db_index=True)),
                (
                    "internal_ip",
                    models.CharField(blank=True, default="", max_length=45),
                ),
                (
                    "external_ip",
                    models.CharField(blank=True, default="", max_length=45),
                ),
                (
                    "mac_address",
                    models.CharField(
                        blank=True, db_index=True, default="", max_length=17
                    ),
                ),
                (
                    "hostname",
                    models.CharField(
                        blank=True, db_index=True, default="", max_length=75
                    ),
                ),
                (
                    "domain",
                    models.CharField(blank=True, default="", max_length=75),
                ),
                (
                    "username",
                    models.CharField(blank=True, default="", max_length=75),
                ),
                (
                    "command",
                    models.TextField(
                        blank=True,
                        default="",
                        validators=[
                            django.core.validators.MaxLengthValidator(254)
                        ],
                    ),
                ),
                (
                    "notes",
                    models.TextField(
                        blank=True,
                        default="",
                        validators=[
                            django.core.validators.MaxLengthValidator(254)
                        ],
                    ),
                ),
                (
                    "filename",
                    models.CharField(blank=True, default="", max_length=254),
                ),
                (
                    "status",
                    models.CharField(blank=True, default="", max_length=75),
                ),
                (
                    "secrets",
                    models.TextField(
                        blank=True,
                        default="",
                        validators=[
                            django.core.validators.MaxLengthValidator(254)
                        ],
                    ),
                ),
                (
                    "hash_algorithm",
                    models.CharField(blank=True, default="", max_length=50),
                ),
                (
                    "hash_value",
                    models.CharField(
                        blank=True, db_index=True, default="", max_length=128
                    ),
                ),
                (
                    "pid",
                    models.CharField(blank=True, default="", max_length=20),
                ),
                (
                    "analyst",
                    models.CharField(
                        blank=True, db_index=True, default="", max_length=100
                    ),
                ),
                ("locked", models.BooleanField(default=False)),
                (
                    "locked_by",
                    models.CharField(blank=True, default="", max_length=100),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "logs",
                "ordering": ["-timestamp", "-id"],
            },
        ),
        migrations.AddIndex(
            model_name="log",
            index=models.Index(
                fields=["-timestamp", "-id"], name="idx_logs_ts_id"
            ),
        ),
        migrations.AddIndex(
            model_name="log",
            index=models.Index(
                fields=["hostname", "timestamp"], name="idx_logs_host_ts"
            ),
        ),
        migrations.AddIndex(
            model_name="log",
            index=models.Index(
                fields=["analyst", "timestamp"], name="idx_logs_analyst_ts"
            ),
        ),
        migrations.AddIndex(
            model_name="log",
            index=models.Index(
                django.db.models.functions.Lower("hash_value"),
                name="idx_logs_hash_lower",
            ),
        ),
    ]
