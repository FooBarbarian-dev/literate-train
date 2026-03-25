from django.db import migrations


DEFAULT_TAGS = [
    # Technique (MITRE ATT&CK)
    ("reconnaissance", "#EF4444", "technique"),
    ("initial-access", "#F97316", "technique"),
    ("execution", "#F59E0B", "technique"),
    ("persistence", "#EAB308", "technique"),
    ("privilege-escalation", "#84CC16", "technique"),
    ("defense-evasion", "#22C55E", "technique"),
    ("credential-access", "#14B8A6", "technique"),
    ("discovery", "#06B6D4", "technique"),
    ("lateral-movement", "#3B82F6", "technique"),
    ("collection", "#6366F1", "technique"),
    ("exfiltration", "#8B5CF6", "technique"),
    ("command-and-control", "#A855F7", "technique"),
    ("impact", "#EC4899", "technique"),
    # Tool
    ("mimikatz", "#DC2626", "tool"),
    ("cobalt-strike", "#EA580C", "tool"),
    ("nmap", "#D97706", "tool"),
    ("bloodhound", "#CA8A04", "tool"),
    ("rubeus", "#65A30D", "tool"),
    ("impacket", "#16A34A", "tool"),
    ("metasploit", "#0D9488", "tool"),
    ("burp-suite", "#0284C7", "tool"),
    ("powershell-empire", "#4F46E5", "tool"),
    ("crackmapexec", "#7C3AED", "tool"),
    ("responder", "#9333EA", "tool"),
    ("certipy", "#C026D3", "tool"),
    ("hashcat", "#DB2777", "tool"),
    ("john-the-ripper", "#E11D48", "tool"),
    ("sliver", "#BE123C", "tool"),
    # Target
    ("domain-controller", "#991B1B", "target"),
    ("workstation", "#9A3412", "target"),
    ("server", "#92400E", "target"),
    ("web-application", "#854D0E", "target"),
    ("database-server", "#3F6212", "target"),
    ("cloud-resource", "#166534", "target"),
    ("network-device", "#115E59", "target"),
    ("email-server", "#1E40AF", "target"),
    ("file-server", "#3730A3", "target"),
    ("vpn-gateway", "#5B21B6", "target"),
    # Status
    ("compromised", "#B91C1C", "status"),
    ("partial-access", "#C2410C", "status"),
    ("failed-attempt", "#A16207", "status"),
    ("access-maintained", "#15803D", "status"),
    ("access-lost", "#6B7280", "status"),
    # Priority
    ("critical", "#DC2626", "priority"),
    ("high", "#F97316", "priority"),
    ("medium", "#EAB308", "priority"),
    ("low", "#6B7280", "priority"),
    # Workflow
    ("needs-review", "#D97706", "workflow"),
    ("follow-up", "#2563EB", "workflow"),
    ("documented", "#16A34A", "workflow"),
    ("reported", "#7C3AED", "workflow"),
    # Evidence
    ("screenshot", "#0EA5E9", "evidence"),
    ("packet-capture", "#8B5CF6", "evidence"),
    ("memory-dump", "#EC4899", "evidence"),
    ("log-file", "#6366F1", "evidence"),
    # Security
    ("sensitive", "#DC2626", "security"),
    ("pii", "#EA580C", "security"),
    ("classified", "#7C2D12", "security"),
    # Operation
    ("phishing", "#2563EB", "operation"),
    ("social-engineering", "#7C3AED", "operation"),
    ("physical-access", "#059669", "operation"),
    ("wireless", "#0891B2", "operation"),
    ("internal", "#4F46E5", "operation"),
    ("external", "#9333EA", "operation"),
]


def seed_tags(apps, schema_editor):
    Tag = apps.get_model("tags", "Tag")
    for name, color, category in DEFAULT_TAGS:
        Tag.objects.get_or_create(
            name=name,
            defaults={
                "color": color,
                "category": category,
                "is_default": True,
                "created_by": "system",
            },
        )


def remove_tags(apps, schema_editor):
    Tag = apps.get_model("tags", "Tag")
    tag_names = [name for name, _, _ in DEFAULT_TAGS]
    Tag.objects.filter(name__in=tag_names, is_default=True).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("tags", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_tags, remove_tags),
    ]
