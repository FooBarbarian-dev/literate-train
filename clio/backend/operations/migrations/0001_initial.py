import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("tags", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Operation",
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
                ("name", models.CharField(max_length=100, unique=True)),
                ("description", models.TextField(blank=True, default="")),
                (
                    "tag_id",
                    models.ForeignKey(
                        blank=True,
                        db_column="tag_id",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="operations",
                        to="tags.tag",
                    ),
                ),
                ("is_active", models.BooleanField(default=True)),
                (
                    "created_by",
                    models.CharField(blank=True, default="", max_length=100),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "operations",
            },
        ),
        migrations.AddIndex(
            model_name="operation",
            index=models.Index(
                fields=["tag_id"], name="idx_ops_tag"
            ),
        ),
        migrations.AddIndex(
            model_name="operation",
            index=models.Index(
                fields=["is_active"], name="idx_ops_is_active"
            ),
        ),
        migrations.CreateModel(
            name="UserOperation",
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
                ("username", models.CharField(max_length=100)),
                (
                    "operation_id",
                    models.ForeignKey(
                        db_column="operation_id",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="user_operations",
                        to="operations.operation",
                    ),
                ),
                ("is_primary", models.BooleanField(default=False)),
                (
                    "assigned_by",
                    models.CharField(blank=True, default="", max_length=100),
                ),
                ("assigned_at", models.DateTimeField(auto_now_add=True)),
                ("last_accessed", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "user_operations",
                "unique_together": {("username", "operation_id")},
            },
        ),
        migrations.AddIndex(
            model_name="useroperation",
            index=models.Index(
                fields=["username"], name="idx_userop_username"
            ),
        ),
        migrations.AddIndex(
            model_name="useroperation",
            index=models.Index(
                fields=["operation_id"], name="idx_userop_op"
            ),
        ),
    ]
