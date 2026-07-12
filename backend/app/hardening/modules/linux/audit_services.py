"""Module d'audit des services Linux actifs (dangereux, obsolètes ou inutiles).

Vérifie que les services à protocole en clair (Telnet, FTP, rsh…) sont
désactivés et que les services de sécurité obligatoires (auditd, rsyslog)
sont actifs, selon le CIS Benchmark Linux v2.0 § 2.
"""
# Référentiel : CIS Benchmark Linux v2.0 — Section 2 (Services)

# Services considérés dangereux (transmission en clair, protocoles obsolètes)
DANGEROUS_SERVICES = [
    # (nom_service, check_id, sévérité, raison)
    ("telnet",        "SVC-001", "CRITICAL", "Telnet transmet les credentials en clair — utiliser SSH"),
    ("vsftpd",        "SVC-002", "HIGH",     "FTP transmet les credentials en clair — utiliser SFTP/FTPS"),
    ("proftpd",       "SVC-002", "HIGH",     "FTP transmet les credentials en clair — utiliser SFTP/FTPS"),
    ("pure-ftpd",     "SVC-002", "HIGH",     "FTP transmet les credentials en clair — utiliser SFTP/FTPS"),
    ("rsh",           "SVC-003", "CRITICAL", "rsh — shell distant non chiffré, remplacé par SSH"),
    ("rlogin",        "SVC-003", "CRITICAL", "rlogin — connexion distante non chiffrée"),
    ("rexec",         "SVC-003", "CRITICAL", "rexec — exécution distante non chiffrée"),
    ("tftp",          "SVC-004", "HIGH",     "TFTP — transfert sans authentification"),
    ("xinetd",        "SVC-005", "MEDIUM",   "xinetd — super-serveur obsolète, surface d'attaque large"),
    ("inetd",         "SVC-005", "MEDIUM",   "inetd — super-serveur obsolète"),
    ("nis",           "SVC-006", "HIGH",     "NIS/YP — authentification réseau non chiffrée"),
    ("ypbind",        "SVC-006", "HIGH",     "NIS client — protocole d'authentification non sécurisé"),
    ("finger",        "SVC-007", "MEDIUM",   "finger — divulgue les infos utilisateurs"),
    ("talk",          "SVC-008", "LOW",      "talk — protocole de messagerie obsolète"),
    ("ntalk",         "SVC-008", "LOW",      "ntalk — protocole de messagerie obsolète"),
    ("chargen",       "SVC-009", "MEDIUM",   "chargen — peut être exploité pour amplification DDoS"),
    ("daytime",       "SVC-009", "LOW",      "daytime — service obsolète"),
    ("discard",       "SVC-009", "LOW",      "discard — service obsolète"),
    ("echo",          "SVC-009", "LOW",      "echo TCP/UDP — peut être exploité"),
    ("time",          "SVC-009", "LOW",      "time — protocole de temps non authentifié"),
    ("rpcbind",       "SVC-010", "MEDIUM",   "rpcbind — exposition inutile si pas de NFS/NIS"),
    ("nfs-server",    "SVC-011", "MEDIUM",   "NFS server — vérifier si nécessaire et sécurisé"),
    ("snmpd",         "SVC-012", "MEDIUM",   "SNMP — vérifier version (v1/v2c = non chiffré)"),
    ("avahi-daemon",  "SVC-013", "LOW",      "avahi/mDNS — inutile sur serveur, divulgue infos réseau"),
    ("cups",          "SVC-014", "LOW",      "CUPS (impression) — inutile sur serveur"),
    ("bluetooth",     "SVC-015", "LOW",      "Bluetooth — inutile sur serveur"),
]

# Services de sécurité qui DOIVENT être actifs
REQUIRED_SECURITY_SERVICES = [
    ("auditd",  "SVC-100", "HIGH",   "auditd — journalisation des événements système (audit trail)"),
    ("rsyslog", "SVC-101", "MEDIUM", "rsyslog/syslog — collecte des logs système"),
]


def _check_service_active(ssh, service_name):
    """Retourne True si le service est actif (systemctl ou SysV)."""
    out, _ = ssh.execute_command(f"systemctl is-active {service_name} 2>/dev/null")
    if out.strip() == "active":
        return True
    # Fallback SysV
    out, _ = ssh.execute_command(f"service {service_name} status 2>/dev/null | grep -c 'running'")
    try:
        return int(out.strip()) > 0
    except ValueError:
        return False


def _check_package_installed(ssh, package_name):
    """Retourne True si le paquet est installé (dpkg ou rpm)."""
    out, _ = ssh.execute_command(f"dpkg -l {package_name} 2>/dev/null | grep -c '^ii'")
    try:
        if int(out.strip()) > 0:
            return True
    except ValueError:
        pass
    out, _ = ssh.execute_command(f"rpm -q {package_name} 2>/dev/null | grep -vc 'not installed'")
    try:
        return int(out.strip()) > 0
    except ValueError:
        return False


def run_audit(ssh, rules):
    """Vérifie les services dangereux et les services de sécurité requis.

    Pour chaque service dangereux de ``DANGEROUS_SERVICES``, contrôle
    s'il est actif via systemctl ou SysV. Vérifie ensuite que les services
    de sécurité de ``REQUIRED_SECURITY_SERVICES`` sont bien démarrés.
    Un check_id en doublon n'est jamais émis deux fois (ex. FTP multi-daemons).

    Args:
        ssh: SSHConnector connecté à la cible.
        rules: dict de règles (non utilisé pour ce module).

    Returns:
        dict avec clés :
            findings (list[dict]) — services dangereux actifs ou services
                                    requis manquants.
            passed   (list[dict]) — contrôles conformes.
            summary  (dict)       — total_checks, passed, failed.
    """
    findings = []
    passed = []

    # --- Services dangereux : vérifier s'ils tournent ---
    seen_check_ids = set()

    for service, check_id, severity, reason in DANGEROUS_SERVICES:
        if check_id in seen_check_ids:
            continue  # Ne pas dupliquer le même check_id

        is_active = _check_service_active(ssh, service)

        if is_active:
            findings.append({
                "check": check_id,
                "check_name": f"service:{service}",
                "description": reason,
                "found": f"{service} actif",
                "expected": "inactif / désinstallé",
                "severity": severity,
                "remediation": f"systemctl stop {service} && systemctl disable {service} && apt-get purge {service} -y 2>/dev/null || yum remove {service} -y",
            })
            seen_check_ids.add(check_id)
        else:
            passed.append({
                "check": check_id,
                "check_name": f"service:{service}",
                "found": f"{service} inactif",
            })
            seen_check_ids.add(check_id)

    # --- Services de sécurité requis : vérifier s'ils tournent ---
    for service, check_id, severity, reason in REQUIRED_SECURITY_SERVICES:
        is_active = _check_service_active(ssh, service)
        if not is_active:
            findings.append({
                "check": check_id,
                "check_name": f"required:{service}",
                "description": reason,
                "found": f"{service} inactif",
                "expected": "actif",
                "severity": severity,
                "remediation": f"systemctl enable --now {service}",
            })
        else:
            passed.append({
                "check": check_id,
                "check_name": f"required:{service}",
                "found": f"{service} actif",
            })

    return {
        "findings": findings,
        "passed": passed,
        "summary": {
            "total_checks": len(findings) + len(passed),
            "passed": len(passed),
            "failed": len(findings),
        }
    }
