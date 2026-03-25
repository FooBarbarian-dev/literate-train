"""
Migration 0003 — BUG 1 + BUG 2/3 fix

BUG 1: ChatSession.thread_id was a UUIDField but django-ai-assistant's Thread
       model uses an integer (BigAutoField) PK.  Django's UUIDField coerced
       integer values via uuid.UUID(int=N), storing e.g. 1 as the UUID
       '00000000-0000-0000-0000-000000000001'.  The reverse lookup
       Thread.objects.get(id='00000000-…') then failed with
       "Field 'id' expected a number but got '…'".

       Fix: change thread_id to BigIntegerField (nullable so that failed
       Thread creations don't block session creation).

BUG 2/3: Add the SessionSource model that records which RAG sources
         (MITRE techniques, NVD CVEs) were cited in each session's replies,
         with source_url populated for MITRE and NVD records.
"""

import django.db.models.deletion
from django.db import migrations, models


def _uuid_to_int(apps, schema_editor):
    """
    Convert existing UUID-encoded thread IDs back to integers.

    When Thread.id=N was stored in a UUIDField, Django used uuid.UUID(int=N)
    producing '00000000-0000-0000-0000-000000000N'.  uuid.UUID(str).int
    reverses that exactly.

    Random UUID4 fallback values will have very large .int values (≥ 2^122);
    we leave those as NULL since they never pointed to a real Thread anyway.
    """
    import uuid as uuid_module

    ChatSession = apps.get_model("threat_intel", "ChatSession")
    for session in ChatSession.objects.all():
        if not session.thread_id:
            continue
        try:
            uid = uuid_module.UUID(str(session.thread_id))
            int_val = uid.int
            # Only keep values that look like real auto-increment PKs.
            # Random UUID4s have int values near 2**122; real PKs are tiny.
            if int_val < 10 ** 9:
                session.thread_id_int = int_val
            # else: leave thread_id_int as NULL — the session was broken anyway.
        except Exception:
            pass
        session.save(update_fields=["thread_id_int"])


class Migration(migrations.Migration):

    dependencies = [
        ("threat_intel", "0002_chatsession"),
    ]

    operations = [
        # ---- Step 1: add temp BigIntegerField alongside old UUIDField ----
        migrations.AddField(
            model_name="chatsession",
            name="thread_id_int",
            field=models.BigIntegerField(null=True, blank=True),
        ),
        # ---- Step 2: data migration — convert UUID values to integers ----
        migrations.RunPython(_uuid_to_int, migrations.RunPython.noop),
        # ---- Step 3: drop the old UUIDField (and its unique constraint) ----
        migrations.RemoveField(
            model_name="chatsession",
            name="thread_id",
        ),
        # ---- Step 4: rename the new int field to thread_id ----
        migrations.RenameField(
            model_name="chatsession",
            old_name="thread_id_int",
            new_name="thread_id",
        ),
        # ---- Step 5: add the unique constraint + final field definition ----
        migrations.AlterField(
            model_name="chatsession",
            name="thread_id",
            field=models.BigIntegerField(
                unique=True,
                null=True,
                blank=True,
                help_text="django-ai-assistant Thread.id (integer PK) backing this session",
            ),
        ),
        # ---- Step 6: create the SessionSource model ----
        migrations.CreateModel(
            name="SessionSource",
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
                    "session",
                    models.ForeignKey(
                        db_index=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="sources",
                        to="threat_intel.chatsession",
                    ),
                ),
                (
                    "source_type",
                    models.CharField(
                        choices=[
                            ("mitre", "MITRE ATT&CK"),
                            ("nvd", "NVD CVE"),
                            ("db", "Django DB"),
                        ],
                        db_index=True,
                        max_length=10,
                    ),
                ),
                (
                    "record_id",
                    models.CharField(
                        max_length=100,
                        help_text="e.g. T1059, CVE-2023-12345, or model name for DB sources",
                    ),
                ),
                (
                    "source_url",
                    models.URLField(
                        blank=True,
                        max_length=500,
                        null=True,
                        help_text="Authoritative URL for this record (null for DB sources)",
                    ),
                ),
                ("retrieved_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "Session Source",
                "verbose_name_plural": "Session Sources",
                "db_table": "threat_intel_session_source",
                "ordering": ["retrieved_at"],
            },
        ),
        migrations.AlterUniqueTogether(
            name="sessionsource",
            unique_together={("session", "source_type", "record_id")},
        ),
    ]
