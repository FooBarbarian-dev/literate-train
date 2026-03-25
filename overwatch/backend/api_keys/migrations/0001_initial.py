import django.db.models.deletion
from django.db import migrations, models


def default_permissions():
    return ["logs:write"]


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("operations", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ApiKey",
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
                ("name", models.CharField(max_length=100)),
                ("key_id", models.CharField(max_length=50, unique=True)),
                ("key_hash", models.CharField(max_length=255)),
                (
                    "created_by",
                    models.CharField(blank=True, default="", max_length=100),
                ),
                (
                    "permissions",
                    models.JSONField(default=default_permissions),
                ),
                ("description", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "expires_at",
                    models.DateTimeField(blank=True, null=True),
                ),
                ("is_active", models.BooleanField(default=True)),
                (
                    "last_used",
                    models.DateTimeField(blank=True, null=True),
                ),
                (
                    "metadata",
                    models.JSONField(blank=True, default=dict),
                ),
                (
                    "operation",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="api_keys",
                        to="operations.operation",
                    ),
                ),
            ],
            options={
                "db_table": "api_keys",
            },
        ),
        migrations.AddIndex(
            model_name="apikey",
            index=models.Index(
                fields=["key_id"], name="idx_apikey_key_id"
            ),
        ),
        migrations.AddIndex(
            model_name="apikey",
            index=models.Index(
                fields=["created_by"], name="idx_apikey_created_by"
            ),
        ),
        migrations.AddIndex(
            model_name="apikey",
            index=models.Index(
                fields=["is_active"], name="idx_apikey_is_active"
            ),
        ),
        migrations.AddIndex(
            model_name="apikey",
            index=models.Index(
                fields=["operation"], name="idx_apikey_operation"
            ),
        ),
    ]
