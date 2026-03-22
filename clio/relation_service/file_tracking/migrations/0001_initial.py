import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
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
