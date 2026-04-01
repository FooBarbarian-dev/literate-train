"""Update Relation model: add relationship_type, change operation_tags to CharField array,
change field sizes, remove pattern_type, update indexes."""

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("relations", "0001_initial"),
    ]

    operations = [
        # 1. Add relationship_type field (nullable initially for backfill)
        migrations.AddField(
            model_name="relation",
            name="relationship_type",
            field=models.CharField(
                max_length=30,
                choices=[
                    ("host", "Host"),
                    ("ip", "IP"),
                    ("domain", "Domain"),
                    ("user_command", "User Command"),
                ],
                default="host",
            ),
            preserve_default=False,
        ),
        # 2. Backfill relationship_type from pattern_type where possible
        migrations.RunSQL(
            sql="""
                UPDATE relations SET relationship_type = CASE
                    WHEN pattern_type = 'host_pattern' THEN 'host'
                    WHEN pattern_type = 'user_pattern' THEN 'user_command'
                    WHEN pattern_type = 'command_sequence' THEN 'user_command'
                    WHEN pattern_type = 'command_cooccurrence' THEN 'user_command'
                    WHEN pattern_type = 'tag_cooccurrence' THEN 'host'
                    WHEN pattern_type = 'tag_sequence' THEN 'host'
                    ELSE 'host'
                END
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
        # 3. Remove old pattern_type field
        migrations.RemoveIndex(
            model_name="relation",
            name="idx_rel_pattern_type",
        ),
        migrations.RemoveField(
            model_name="relation",
            name="pattern_type",
        ),
        # 4. Remove old indexes
        migrations.RemoveIndex(
            model_name="relation",
            name="idx_rel_source",
        ),
        migrations.RemoveIndex(
            model_name="relation",
            name="idx_rel_target",
        ),
        migrations.RemoveIndex(
            model_name="relation",
            name="idx_rel_last_seen",
        ),
        # 5. Alter source_type, source_value, target_type, target_value field sizes
        migrations.AlterField(
            model_name="relation",
            name="source_type",
            field=models.CharField(
                max_length=20,
                choices=[
                    ("hostname", "Hostname"),
                    ("ip", "IP"),
                    ("domain", "Domain"),
                    ("username", "Username"),
                ],
            ),
        ),
        migrations.AlterField(
            model_name="relation",
            name="source_value",
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name="relation",
            name="target_type",
            field=models.CharField(
                max_length=20,
                choices=[
                    ("hostname", "Hostname"),
                    ("ip", "IP"),
                    ("domain", "Domain"),
                    ("command", "Command"),
                ],
            ),
        ),
        migrations.AlterField(
            model_name="relation",
            name="target_value",
            field=models.CharField(max_length=255),
        ),
        # 6. Change strength and connection_count to PositiveIntegerField
        migrations.AlterField(
            model_name="relation",
            name="strength",
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.AlterField(
            model_name="relation",
            name="connection_count",
            field=models.PositiveIntegerField(default=1),
        ),
        # 7. Change operation_tags from IntegerField array to CharField array
        migrations.AlterField(
            model_name="relation",
            name="operation_tags",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(max_length=255),
                blank=True,
                default=list,
                size=None,
            ),
        ),
        # 8. Add new indexes
        migrations.AddIndex(
            model_name="relation",
            index=models.Index(fields=["source_type"], name="idx_rel_source_type"),
        ),
        migrations.AddIndex(
            model_name="relation",
            index=models.Index(fields=["target_type"], name="idx_rel_target_type"),
        ),
        migrations.AddIndex(
            model_name="relation",
            index=models.Index(fields=["relationship_type"], name="idx_rel_rel_type"),
        ),
    ]
