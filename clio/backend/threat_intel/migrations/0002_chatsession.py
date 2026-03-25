import uuid

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("threat_intel", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ChatSession",
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
                    "thread_id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        help_text="django-ai-assistant Thread.id backing this session",
                        unique=True,
                    ),
                ),
                (
                    "username",
                    models.CharField(
                        db_index=True,
                        help_text="JWTUser.username who owns this session",
                        max_length=150,
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        blank=True,
                        default="",
                        help_text="Display name; set from first 60 chars of first user message",
                        max_length=255,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Chat Session",
                "verbose_name_plural": "Chat Sessions",
                "db_table": "threat_intel_chat_session",
                "ordering": ["-updated_at"],
            },
        ),
    ]
