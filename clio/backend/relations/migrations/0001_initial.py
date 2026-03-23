import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        # -----------------------------------------------------------------
        # Relation
        # -----------------------------------------------------------------
        migrations.CreateModel(
            name="Relation",
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
                ("source_type", models.CharField(max_length=50)),
                ("source_value", models.TextField()),
                ("target_type", models.CharField(max_length=50)),
                ("target_value", models.TextField()),
                ("strength", models.IntegerField(default=1)),
                ("connection_count", models.IntegerField(default=1)),
                (
                    "pattern_type",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("command_sequence", "Command Sequence"),
                            ("command_cooccurrence", "Command Co-occurrence"),
                            ("user_pattern", "User Pattern"),
                            ("host_pattern", "Host Pattern"),
                            ("tag_cooccurrence", "Tag Co-occurrence"),
                            ("tag_sequence", "Tag Sequence"),
                        ],
                        max_length=50,
                        null=True,
                    ),
                ),
                ("first_seen", models.DateTimeField(auto_now_add=True)),
                ("last_seen", models.DateTimeField(auto_now=True)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                (
                    "operation_tags",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.IntegerField(),
                        blank=True,
                        default=list,
                        size=None,
                    ),
                ),
                (
                    "source_log_ids",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.IntegerField(),
                        blank=True,
                        default=list,
                        size=None,
                    ),
                ),
            ],
            options={
                "db_table": "relations",
            },
        ),
        migrations.AddConstraint(
            model_name="relation",
            constraint=models.UniqueConstraint(
                fields=("source_type", "source_value", "target_type", "target_value"),
                name="uq_relation_source_target",
            ),
        ),
        migrations.AddIndex(
            model_name="relation",
            index=models.Index(
                fields=["source_type", "source_value"], name="idx_rel_source"
            ),
        ),
        migrations.AddIndex(
            model_name="relation",
            index=models.Index(
                fields=["target_type", "target_value"], name="idx_rel_target"
            ),
        ),
        migrations.AddIndex(
            model_name="relation",
            index=models.Index(fields=["pattern_type"], name="idx_rel_pattern_type"),
        ),
        migrations.AddIndex(
            model_name="relation",
            index=models.Index(fields=["last_seen"], name="idx_rel_last_seen"),
        ),
        migrations.AddIndex(
            model_name="relation",
            index=models.Index(
                fields=["operation_tags"],
                name="idx_rel_operation_tags",
                opclasses=["gin__int_ops"],
            ),
        ),
        migrations.AddIndex(
            model_name="relation",
            index=models.Index(
                fields=["source_log_ids"],
                name="idx_rel_source_log_ids",
                opclasses=["gin__int_ops"],
            ),
        ),
        # -----------------------------------------------------------------
        # LogRelationship
        # -----------------------------------------------------------------
        migrations.CreateModel(
            name="LogRelationship",
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
                ("source_id", models.IntegerField(db_index=True)),
                ("target_id", models.IntegerField(db_index=True)),
                (
                    "type",
                    models.CharField(
                        choices=[
                            ("parent_child", "Parent-Child"),
                            ("linked", "Linked"),
                            ("dependency", "Dependency"),
                            ("correlation", "Correlation"),
                        ],
                        max_length=50,
                    ),
                ),
                ("relationship", models.CharField(blank=True, default="", max_length=100)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("created_by", models.CharField(blank=True, default="", max_length=100)),
                ("notes", models.TextField(blank=True, default="")),
            ],
            options={
                "db_table": "log_relationships",
            },
        ),
        migrations.AddIndex(
            model_name="logrelationship",
            index=models.Index(
                fields=["source_id", "target_id"], name="idx_lr_src_tgt"
            ),
        ),
        migrations.AddIndex(
            model_name="logrelationship",
            index=models.Index(fields=["type"], name="idx_lr_type"),
        ),
        # -----------------------------------------------------------------
        # TagRelationship
        # -----------------------------------------------------------------
        migrations.CreateModel(
            name="TagRelationship",
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
                ("source_tag_id", models.IntegerField(db_index=True)),
                ("target_tag_id", models.IntegerField(db_index=True)),
                ("cooccurrence_count", models.IntegerField(default=1)),
                ("sequence_count", models.IntegerField(default=0)),
                ("correlation_strength", models.FloatField(default=0.0)),
                ("first_seen", models.DateTimeField(auto_now_add=True)),
                ("last_seen", models.DateTimeField(auto_now=True)),
                ("metadata", models.JSONField(blank=True, default=dict)),
            ],
            options={
                "db_table": "tag_relationships",
            },
        ),
        migrations.AddIndex(
            model_name="tagrelationship",
            index=models.Index(
                fields=["source_tag_id", "target_tag_id"], name="idx_tr_src_tgt"
            ),
        ),
        migrations.AddIndex(
            model_name="tagrelationship",
            index=models.Index(fields=["correlation_strength"], name="idx_tr_corr"),
        ),
        # -----------------------------------------------------------------
        # FileStatus
        # -----------------------------------------------------------------
        migrations.CreateModel(
            name="FileStatus",
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
                ("filename", models.CharField(max_length=254)),
                ("status", models.CharField(blank=True, default="", max_length=50)),
                ("hash_algorithm", models.CharField(blank=True, default="", max_length=50)),
                ("hash_value", models.CharField(blank=True, default="", max_length=128)),
                ("hostname", models.CharField(blank=True, default="", max_length=75)),
                ("internal_ip", models.CharField(blank=True, default="", max_length=45)),
                ("external_ip", models.CharField(blank=True, default="", max_length=45)),
                ("mac_address", models.CharField(blank=True, default="", max_length=17)),
                ("username", models.CharField(blank=True, default="", max_length=75)),
                ("analyst", models.CharField(blank=True, default="", max_length=100)),
                ("notes", models.TextField(blank=True, default="")),
                ("command", models.TextField(blank=True, default="")),
                ("secrets", models.TextField(blank=True, default="")),
                ("first_seen", models.DateTimeField(auto_now_add=True)),
                ("last_seen", models.DateTimeField(auto_now=True)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                (
                    "operation_tags",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.IntegerField(),
                        blank=True,
                        default=list,
                        size=None,
                    ),
                ),
                (
                    "source_log_ids",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.IntegerField(),
                        blank=True,
                        default=list,
                        size=None,
                    ),
                ),
            ],
            options={
                "db_table": "file_status",
            },
        ),
        migrations.AddConstraint(
            model_name="filestatus",
            constraint=models.UniqueConstraint(
                fields=("filename", "hostname", "internal_ip"),
                name="uq_file_status_file_host_ip",
            ),
        ),
        migrations.AddIndex(
            model_name="filestatus",
            index=models.Index(fields=["filename"], name="idx_fs_filename"),
        ),
        migrations.AddIndex(
            model_name="filestatus",
            index=models.Index(fields=["hostname"], name="idx_fs_hostname"),
        ),
        migrations.AddIndex(
            model_name="filestatus",
            index=models.Index(fields=["status"], name="idx_fs_status"),
        ),
        migrations.AddIndex(
            model_name="filestatus",
            index=models.Index(fields=["hash_value"], name="idx_fs_hash_value"),
        ),
        # -----------------------------------------------------------------
        # FileStatusHistory
        # -----------------------------------------------------------------
        migrations.CreateModel(
            name="FileStatusHistory",
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
                ("filename", models.CharField(max_length=254)),
                ("status", models.CharField(blank=True, default="", max_length=50)),
                ("previous_status", models.CharField(blank=True, default="", max_length=50)),
                ("hash_algorithm", models.CharField(blank=True, default="", max_length=50)),
                ("hash_value", models.CharField(blank=True, default="", max_length=128)),
                ("hostname", models.CharField(blank=True, default="", max_length=75)),
                ("internal_ip", models.CharField(blank=True, default="", max_length=45)),
                ("external_ip", models.CharField(blank=True, default="", max_length=45)),
                ("mac_address", models.CharField(blank=True, default="", max_length=17)),
                ("username", models.CharField(blank=True, default="", max_length=75)),
                ("analyst", models.CharField(blank=True, default="", max_length=100)),
                ("notes", models.TextField(blank=True, default="")),
                ("command", models.TextField(blank=True, default="")),
                ("secrets", models.TextField(blank=True, default="")),
                ("timestamp", models.DateTimeField(auto_now_add=True)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                (
                    "operation_tags",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.IntegerField(),
                        blank=True,
                        default=list,
                        size=None,
                    ),
                ),
                (
                    "source_log_ids",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.IntegerField(),
                        blank=True,
                        default=list,
                        size=None,
                    ),
                ),
            ],
            options={
                "db_table": "file_status_history",
                "ordering": ["-timestamp"],
            },
        ),
        migrations.AddIndex(
            model_name="filestatushistory",
            index=models.Index(fields=["filename"], name="idx_fsh_filename"),
        ),
        migrations.AddIndex(
            model_name="filestatushistory",
            index=models.Index(fields=["-timestamp"], name="idx_fsh_timestamp"),
        ),
        migrations.AddIndex(
            model_name="filestatushistory",
            index=models.Index(fields=["hostname"], name="idx_fsh_hostname"),
        ),
    ]
