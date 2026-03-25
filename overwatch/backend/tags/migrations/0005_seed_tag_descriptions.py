from django.db import migrations


TAG_DESCRIPTIONS = {
    # Technique (MITRE ATT&CK)
    "reconnaissance": "Gathering information to plan future adversary operations (MITRE ATT&CK TA0043).",
    "initial-access": "Techniques to gain a foothold in the target network (MITRE ATT&CK TA0001).",
    "execution": "Running adversary-controlled code on a local or remote system (MITRE ATT&CK TA0002).",
    "persistence": "Maintaining a foothold across restarts, changed credentials, or other interruptions (MITRE ATT&CK TA0003).",
    "privilege-escalation": "Gaining higher-level permissions on a system or network (MITRE ATT&CK TA0004).",
    "defense-evasion": "Avoiding detection throughout the compromise (MITRE ATT&CK TA0005).",
    "credential-access": "Stealing credentials such as account names and passwords (MITRE ATT&CK TA0006).",
    "discovery": "Learning about the environment to understand what can be controlled (MITRE ATT&CK TA0007).",
    "lateral-movement": "Pivoting through the environment to reach additional hosts (MITRE ATT&CK TA0008).",
    "collection": "Gathering data of interest before exfiltration (MITRE ATT&CK TA0009).",
    "exfiltration": "Stealing data from the target network (MITRE ATT&CK TA0010).",
    "command-and-control": "Communicating with compromised systems to control them (MITRE ATT&CK TA0011).",
    "impact": "Manipulating, interrupting, or destroying systems and data (MITRE ATT&CK TA0040).",
    # Tool
    "mimikatz": "Post-exploitation tool for extracting plaintext passwords, hashes, and Kerberos tickets from Windows memory.",
    "cobalt-strike": "Commercial adversary-simulation framework widely used in red team operations and by threat actors.",
    "nmap": "Network mapper used for host discovery, port scanning, and service/OS fingerprinting.",
    "bloodhound": "Active Directory attack-path analysis tool that visualises relationships and finds privilege-escalation paths.",
    "rubeus": "C# toolset for Kerberos abuse including AS-REP roasting, Pass-the-Ticket, and Kerberoasting.",
    "impacket": "Python library providing low-level access to network protocols; used for SMB, DCOM, and Kerberos attacks.",
    "metasploit": "Open-source penetration testing framework providing exploits, payloads, and post-exploitation modules.",
    "burp-suite": "Web application security testing platform with an intercepting proxy and active/passive scanner.",
    "powershell-empire": "Post-exploitation framework built on PowerShell and Python agents with a modular plugin system.",
    "crackmapexec": "Swiss-army knife for network pentesting against SMB, WinRM, LDAP, and MSSQL at scale.",
    "responder": "LLMNR/NBT-NS/MDNS poisoner used to capture Net-NTLMv2 hashes on local network segments.",
    "certipy": "Tool for enumerating and abusing Active Directory Certificate Services misconfigurations.",
    "hashcat": "Advanced GPU-accelerated password recovery tool supporting hundreds of hash types.",
    "john-the-ripper": "Classic open-source password cracker supporting many hash formats and wordlist/rule attacks.",
    "sliver": "Open-source adversary-simulation framework with mTLS, WireGuard, and HTTP/S C2 channels.",
    # Target
    "domain-controller": "Activity targeting or originating from a Windows Domain Controller.",
    "workstation": "Activity targeting or originating from a user workstation endpoint.",
    "server": "Activity targeting or originating from a generic server (non-DC, non-web).",
    "web-application": "Activity targeting a web application or web-facing service.",
    "database-server": "Activity targeting or originating from a database server (SQL, NoSQL, etc.).",
    "cloud-resource": "Activity targeting cloud-hosted infrastructure, storage, or services.",
    "network-device": "Activity targeting routers, switches, firewalls, or other network infrastructure.",
    "email-server": "Activity targeting or originating from an email/SMTP server.",
    "file-server": "Activity targeting or originating from a file share or NAS device.",
    "vpn-gateway": "Activity targeting or originating from a VPN concentrator or gateway.",
    # Status
    "compromised": "The asset or account has been fully compromised by the adversary.",
    "partial-access": "The adversary has limited or partial access to the asset or account.",
    "failed-attempt": "An adversary action was attempted but did not succeed.",
    "access-maintained": "Persistent access to the target is still active.",
    "access-lost": "Previously established access has been revoked or lost.",
    # Priority
    "critical": "Requires immediate attention — high-impact finding or active threat.",
    "high": "Significant finding that should be addressed in the current engagement phase.",
    "medium": "Moderate-impact finding warranting follow-up after higher priorities.",
    "low": "Minor finding or informational observation with limited impact.",
    # Workflow
    "needs-review": "Log or finding requires analyst review before further action.",
    "follow-up": "A follow-up action or investigation is required for this activity.",
    "documented": "The activity has been documented in the engagement record.",
    "reported": "The finding has been formally reported to the client or stakeholder.",
    # Evidence
    "screenshot": "A screenshot was captured as evidence for this activity.",
    "packet-capture": "Network packet capture (PCAP) was collected as evidence.",
    "memory-dump": "A memory dump was obtained from the target system.",
    "log-file": "Log file evidence was collected to support this finding.",
    # Security
    "sensitive": "Involves sensitive data or systems requiring careful handling.",
    "pii": "Personally identifiable information was accessed or exposed.",
    "classified": "Activity involves classified or restricted information assets.",
    # Operation
    "phishing": "Activity related to a phishing campaign or email-based initial access vector.",
    "social-engineering": "Activity involving manipulation of individuals rather than technical exploitation.",
    "physical-access": "Activity requiring or involving physical presence at a target facility.",
    "wireless": "Activity targeting or exploiting wireless networks (Wi-Fi, Bluetooth, etc.).",
    "internal": "Activity conducted from inside the target network perimeter.",
    "external": "Activity conducted from outside the target network perimeter.",
}


def add_descriptions(apps, schema_editor):
    Tag = apps.get_model("tags", "Tag")
    for name, description in TAG_DESCRIPTIONS.items():
        Tag.objects.filter(name=name, is_default=True).update(description=description)


def remove_descriptions(apps, schema_editor):
    Tag = apps.get_model("tags", "Tag")
    Tag.objects.filter(name__in=TAG_DESCRIPTIONS.keys(), is_default=True).update(description="")


class Migration(migrations.Migration):

    dependencies = [
        ("tags", "0004_unique_constraint"),
    ]

    operations = [
        migrations.RunPython(add_descriptions, remove_descriptions),
    ]
