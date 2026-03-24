"""
Seed the database with realistic C2 framework session logs.

Usage:
    python manage.py seed_c2_logs                   # seed all profiles
    python manage.py seed_c2_logs --profile sliver   # seed one profile
    python manage.py seed_c2_logs --list              # list available profiles
    python manage.py seed_c2_logs --clear             # wipe C2 demo data first

Each C2 profile (Sliver, Cobalt Strike, etc.) generates a realistic
sequence of operator log entries covering the full attack lifecycle:
implant generation, initial callback, discovery, privilege escalation,
credential access, lateral movement, and persistence.

All IPs, hostnames, and credentials are fictional.
"""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from ingest.c2_profiles import PROFILES
from logs.models import Log
from operations.models import Operation, UserOperation
from tags.models import LogTag, Tag

# Analysts used by C2 seeder — used for --clear
C2_ANALYSTS = {"c2-operator1", "c2-operator2"}


class Command(BaseCommand):
    help = "Seed database with realistic C2 framework session logs"

    def add_arguments(self, parser):
        parser.add_argument(
            "--profile",
            type=str,
            choices=list(PROFILES.keys()),
            help="Seed only a specific C2 profile (default: all)",
        )
        parser.add_argument(
            "--list",
            action="store_true",
            help="List available C2 profiles and exit",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Remove existing C2 demo data before seeding",
        )

    def handle(self, *args, **options):
        if options["list"]:
            self._list_profiles()
            return

        if options["clear"]:
            self._clear_c2_data()

        profiles = (
            {options["profile"]: PROFILES[options["profile"]]}
            if options.get("profile")
            else PROFILES
        )

        total = 0
        for name, profile in profiles.items():
            count = self._seed_profile(name, profile)
            total += count

        self.stdout.write(
            self.style.SUCCESS(f"C2 log seeding complete — {total} logs created")
        )

    def _list_profiles(self):
        self.stdout.write("Available C2 profiles:\n")
        for key, profile in PROFILES.items():
            self.stdout.write(f"  {key:20s} {profile['description']}")

    def _clear_c2_data(self):
        # Collect operation names from all profiles
        op_names = [p["default_operation"]["name"] for p in PROFILES.values()]
        Log.objects.filter(analyst__in=C2_ANALYSTS).delete()
        Operation.objects.filter(name__in=op_names).delete()
        op_tag_names = [f"op:{name.lower()}" for name in op_names]
        Tag.objects.filter(name__in=op_tag_names).delete()
        self.stdout.write(self.style.WARNING("Cleared existing C2 demo data"))

    def _seed_profile(self, profile_key, profile):
        self.stdout.write(f"\n--- Seeding {profile['name']} ---")

        # Create operation
        op_data = profile["default_operation"]
        op, created = Operation.objects.get_or_create(
            name=op_data["name"],
            defaults={
                "description": op_data["description"],
                "created_by": "admin",
            },
        )
        if created:
            for username, is_primary in [("admin", True), ("user", False)]:
                UserOperation.objects.get_or_create(
                    username=username,
                    operation=op,
                    defaults={
                        "is_primary": is_primary,
                        "assigned_by": "system",
                    },
                )
            self.stdout.write(f"  Created operation: {op.name}")
        else:
            self.stdout.write(f"  Operation already exists: {op.name}")

        # Generate logs from profile
        log_entries = profile["generate"](
            analyst=profile["default_analyst"],
            operation_name=op_data["name"],
        )

        # Collect all needed tag names
        all_tag_names = set()
        for entry in log_entries:
            all_tag_names.update(entry.get("tags", []))

        existing_tags = {t.name: t for t in Tag.objects.filter(name__in=all_tag_names)}
        for tag_name in all_tag_names:
            if tag_name not in existing_tags:
                tag = Tag.objects.create(
                    name=tag_name,
                    category="tool" if tag_name in PROFILES else "technique",
                    is_default=False,
                    created_by="system",
                )
                existing_tags[tag_name] = tag

        # Get operation tag
        op.refresh_from_db()
        op_tag = getattr(op, "tag", None)

        now = timezone.now()
        count = 0

        for entry in log_entries:
            ts = now + timedelta(hours=entry["timestamp_offset_hours"])
            log, created = Log.objects.get_or_create(
                hostname=entry["hostname"],
                command=entry["command"],
                analyst=entry["analyst"],
                defaults={
                    "timestamp": ts,
                    "internal_ip": entry.get("internal_ip", ""),
                    "external_ip": entry.get("external_ip", ""),
                    "domain": entry.get("domain", ""),
                    "username": entry.get("username", ""),
                    "notes": entry.get("notes", ""),
                    "status": entry.get("status", ""),
                    "pid": entry.get("pid", ""),
                    "filename": entry.get("filename", ""),
                    "hash_value": entry.get("hash_value", ""),
                    "hash_algorithm": entry.get("hash_algorithm", ""),
                },
            )

            if created:
                for tag_name in entry.get("tags", []):
                    tag = existing_tags[tag_name]
                    LogTag.objects.get_or_create(
                        log=log, tag=tag, defaults={"tagged_by": "system"}
                    )
                if op_tag:
                    LogTag.objects.get_or_create(
                        log=log, tag=op_tag, defaults={"tagged_by": "system"}
                    )
                count += 1
                cmd_preview = entry["command"][:70]
                self.stdout.write(f"  + {cmd_preview}...")
            else:
                if op_tag:
                    LogTag.objects.get_or_create(
                        log=log, tag=op_tag, defaults={"tagged_by": "system"}
                    )
                self.stdout.write(
                    f"  (exists) {entry['command'][:70]}..."
                )

        self.stdout.write(f"  {profile['name']}: {count} new logs")
        return count
