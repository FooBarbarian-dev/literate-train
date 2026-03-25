import django.db.models.deletion
import django.db.models.functions
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("logs", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Tag",
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
                ("name", models.CharField(max_length=50, unique=True)),
                (
                    "color",
                    models.CharField(default="#6B7280", max_length=7),
                ),
                (
                    "category",
                    models.CharField(blank=True, default="", max_length=50),
                ),
                ("description", models.TextField(blank=True, default="")),
                ("is_default", models.BooleanField(default=False)),
                (
                    "created_by",
                    models.CharField(blank=True, default="", max_length=100),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "tags",
            },
        ),
        migrations.AddIndex(
            model_name="tag",
            index=models.Index(
                django.db.models.functions.Lower("name"),
                name="idx_tags_name_lower",
            ),
        ),
        migrations.AddIndex(
            model_name="tag",
            index=models.Index(
                fields=["category"], name="idx_tags_category"
            ),
        ),
        migrations.AddIndex(
            model_name="tag",
            index=models.Index(
                fields=["is_default"], name="idx_tags_is_default"
            ),
        ),
        migrations.CreateModel(
            name="LogTag",
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
                    "tagged_by",
                    models.CharField(blank=True, default="", max_length=100),
                ),
                ("tagged_at", models.DateTimeField(auto_now_add=True)),
                (
                    "log",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="log_tags",
                        to="logs.log",
                    ),
                ),
                (
                    "tag",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="log_tags",
                        to="tags.tag",
                    ),
                ),
            ],
            options={
                "db_table": "log_tags",
                "unique_together": {("log", "tag")},
            },
        ),
        migrations.AddIndex(
            model_name="logtag",
            index=models.Index(fields=["log"], name="idx_logtag_log"),
        ),
        migrations.AddIndex(
            model_name="logtag",
            index=models.Index(fields=["tag"], name="idx_logtag_tag"),
        ),
        migrations.AddIndex(
            model_name="logtag",
            index=models.Index(
                fields=["tagged_at"], name="idx_logtag_tagged_at"
            ),
        ),
    ]
