"""Module d'audit de la gestion des paquets et de la maintenance système Linux.

Implémente les recommandations ANSSI-BP-028 v2.0 § 6.5-6.6 : suppression des
paquets inutiles (R58), vérification des dépôts APT/YUM (R59) et contrôle
des mises à jour de sécurité en attente (R61).
"""
# Référentiel : ANSSI-BP-028 v2.0 — Section 6.5-6.6
# Checks : R58 (paquets strictement nécessaires), R59 (dépôts de confiance), R61 (mises à jour)

# Paquets considérés inutiles sur un serveur durci
UNNECESSARY_PACKAGES = [
    ("telnet",       "CRITICAL", "R58", "Protocole non chiffré — remplacer par SSH"),
    ("rsh-client",   "CRITICAL", "R58", "Remote Shell non chiffré"),
    ("rsh-server",   "CRITICAL", "R58", "Remote Shell serveur non chiffré"),
    ("nis",          "HIGH",     "R58", "NIS/YP — authentification réseau non chiffrée"),
    ("tftp",         "HIGH",     "R58", "TFTP — transfert sans authentification"),
    ("talk",         "MEDIUM",   "R58", "Messagerie en clair — obsolète"),
    ("ntalk",        "MEDIUM",   "R58", "Messagerie en clair — obsolète"),
    ("xinetd",       "MEDIUM",   "R58", "Super-serveur obsolète, surface d'attaque large"),
    ("inetd",        "MEDIUM",   "R58", "Super-serveur obsolète"),
    ("cups",         "LOW",      "R58", "Service impression — inutile sur serveur"),
    ("avahi-daemon", "LOW",      "R58", "mDNS — fuite d'informations réseau"),
    ("whoopsie",     "LOW",      "R58", "Service de rapport de plantages Ubuntu"),
    ("apport",       "LOW",      "R58", "Service de rapport de plantages Ubuntu"),
    ("popularity-contest","LOW", "R58", "Collecte de données d'utilisation"),
]


def _is_installed(ssh, package):
    """Vérifie si un paquet est installé (dpkg ou rpm)."""
    # Debian/Ubuntu
    out, _ = ssh.execute_command(f"dpkg -l {package} 2>/dev/null | grep -c '^ii'")
    try:
        if int(out.strip()) > 0:
            return True
    except ValueError:
        pass
    # RHEL/CentOS
    out, _ = ssh.execute_command(f"rpm -q {package} 2>/dev/null | grep -vc 'not installed'")
    try:
        return int(out.strip()) > 0
    except ValueError:
        return False


def _r58_unnecessary_packages(ssh):
    """R58 — N'installer que les paquets strictement nécessaires."""
    findings, passed = [], []

    for package, severity, ref, reason in UNNECESSARY_PACKAGES:
        if _is_installed(ssh, package):
            findings.append({
                "check": f"PKG-R58-{package.upper().replace('-','_')}",
                "check_name": f"Paquet inutile : {package}",
                "description": f"[ANSSI {ref}] Le paquet '{package}' est installé mais non nécessaire — {reason}",
                "found": f"{package} installé",
                "expected": f"{package} non installé",
                "severity": severity,
                "remediation": f"apt purge {package} -y  # ou  yum remove {package} -y",
            })
        else:
            passed.append({
                "check": f"PKG-R58-{package.upper().replace('-','_')}",
                "check_name": f"Paquet absent : {package}",
                "found": f"{package} non installé ✓",
            })

    return findings, passed


def _r59_trusted_repos(ssh):
    """R59 — Utiliser uniquement des dépôts de confiance."""
    findings, passed = [], []

    # Vérifier les sources Debian/Ubuntu
    out, _ = ssh.execute_command(
        "grep -rE '^deb ' /etc/apt/sources.list /etc/apt/sources.list.d/ 2>/dev/null | "
        "grep -vE '(debian|ubuntu|security|archive|backports|updates)' | grep -v '#'"
    )
    unofficial_apt = [l.strip() for l in out.strip().splitlines() if l.strip()]

    if unofficial_apt:
        findings.append({
            "check": "PKG-R59-001",
            "check_name": "Dépôts APT non officiels",
            "description": "[ANSSI R59] Des dépôts de paquets non officiels sont configurés — "
                           "risque d'installation de paquets compromis ou non vérifiés",
            "found": f"{len(unofficial_apt)} dépôt(s) non officiel(s) : {unofficial_apt[0][:100]}",
            "expected": "Uniquement les dépôts officiels de la distribution",
            "severity": "HIGH",
            "remediation": "Supprimer les dépôts tiers dans /etc/apt/sources.list.d/ et vérifier /etc/apt/sources.list",
        })
    else:
        # Vérifier si apt est disponible et a des sources
        out2, _ = ssh.execute_command("cat /etc/apt/sources.list 2>/dev/null | grep -c '^deb'")
        try:
            if int(out2.strip()) > 0:
                passed.append({
                    "check": "PKG-R59-001",
                    "check_name": "Dépôts APT",
                    "found": "Seuls les dépôts officiels sont configurés",
                })
        except ValueError:
            pass

    # Vérifier les dépôts yum/dnf (RHEL)
    out, _ = ssh.execute_command("ls /etc/yum.repos.d/ 2>/dev/null")
    if out.strip():
        out2, _ = ssh.execute_command(
            "grep -rE '^baseurl=' /etc/yum.repos.d/ 2>/dev/null | "
            "grep -vE '(redhat|centos|fedora|rockylinux|almalinux|rhel)' | head -5"
        )
        unofficial_yum = [l.strip() for l in out2.strip().splitlines() if l.strip()]
        if unofficial_yum:
            findings.append({
                "check": "PKG-R59-002",
                "check_name": "Dépôts YUM/DNF non officiels",
                "description": "[ANSSI R59] Des dépôts yum/dnf non officiels sont configurés",
                "found": ", ".join(unofficial_yum[:3]),
                "expected": "Uniquement les dépôts officiels RedHat/CentOS",
                "severity": "HIGH",
                "remediation": "Supprimer ou désactiver les dépôts tiers dans /etc/yum.repos.d/",
            })
        else:
            passed.append({
                "check": "PKG-R59-002",
                "check_name": "Dépôts YUM/DNF",
                "found": "Seuls les dépôts officiels YUM/DNF configurés",
            })

    return findings, passed


def _r61_security_updates(ssh):
    """R61 — Effectuer des mises à jour de sécurité régulières."""
    findings, passed = [], []

    # Vérifier les mises à jour disponibles (Debian/Ubuntu)
    out, _ = ssh.execute_command(
        "apt-get --just-print upgrade 2>/dev/null | grep -c '^Inst' || echo 0"
    )
    try:
        pending = int(out.strip())
        if pending > 0:
            # Distinguer les mises à jour de sécurité
            out2, _ = ssh.execute_command(
                "apt-get --just-print upgrade 2>/dev/null | grep 'security' | head -10"
            )
            security_updates = [l for l in out2.strip().splitlines() if l]
            severity = "CRITICAL" if len(security_updates) > 0 else "MEDIUM"
            findings.append({
                "check": "PKG-R61-001",
                "check_name": "Mises à jour en attente",
                "description": f"[ANSSI R61] {pending} paquet(s) nécessitent une mise à jour — "
                               f"dont {len(security_updates)} mise(s) à jour de sécurité",
                "found": f"{pending} mises à jour disponibles ({len(security_updates)} sécurité)",
                "expected": "Système à jour",
                "severity": severity,
                "remediation": "apt-get update && apt-get upgrade -y  # ou unattended-upgrades pour l'automatisation",
            })
        else:
            passed.append({
                "check": "PKG-R61-001",
                "check_name": "Mises à jour système",
                "found": "Système à jour — aucune mise à jour en attente",
            })
    except ValueError:
        # Essayer yum/dnf
        out, _ = ssh.execute_command("yum check-update 2>/dev/null | grep -c '^[a-zA-Z]' || echo 0")
        try:
            pending = max(0, int(out.strip()) - 1)  # première ligne = header
            if pending > 0:
                findings.append({
                    "check": "PKG-R61-001",
                    "check_name": "Mises à jour en attente (YUM)",
                    "description": f"[ANSSI R61] {pending} paquet(s) nécessitent une mise à jour",
                    "found": f"{pending} mises à jour disponibles",
                    "expected": "Système à jour",
                    "severity": "MEDIUM",
                    "remediation": "yum update -y  # ou dnf update -y",
                })
            else:
                passed.append({
                    "check": "PKG-R61-001",
                    "check_name": "Mises à jour système (YUM)",
                    "found": "Système à jour",
                })
        except ValueError:
            pass

    # Vérifier si les mises à jour automatiques de sécurité sont configurées
    out, _ = ssh.execute_command("dpkg -l unattended-upgrades 2>/dev/null | grep -c '^ii'")
    try:
        if int(out.strip()) > 0:
            # Vérifier la config
            out2, _ = ssh.execute_command(
                "grep -E '^Unattended-Upgrade::Automatic-Reboot|^APT::Periodic::Unattended-Upgrade' "
                "/etc/apt/apt.conf.d/50unattended-upgrades 2>/dev/null | head -3"
            )
            passed.append({
                "check": "PKG-R61-002",
                "check_name": "Mises à jour automatiques",
                "found": "unattended-upgrades installé et configuré",
            })
        else:
            findings.append({
                "check": "PKG-R61-002",
                "check_name": "Mises à jour automatiques absentes",
                "description": "[ANSSI R61] Pas de système de mises à jour automatiques de sécurité — "
                               "les correctifs de sécurité doivent être appliqués manuellement",
                "found": "unattended-upgrades non installé",
                "expected": "unattended-upgrades installé et configuré",
                "severity": "MEDIUM",
                "remediation": "apt install unattended-upgrades && dpkg-reconfigure unattended-upgrades",
            })
    except ValueError:
        pass

    return findings, passed


def run_audit(ssh, rules):
    """Audite la gestion des paquets et les mises à jour système.

    Enchaîne les vérifications R58 (paquets inutiles), R59 (dépôts),
    R61 (mises à jour en attente) et agrège les résultats.

    Args:
        ssh: SSHConnector connecté à la cible.
        rules: dict de règles (non utilisé pour ce module).

    Returns:
        dict avec clés :
            findings (list[dict]) — paquets dangereux présents, dépôts non
                                    officiels ou mises à jour manquantes.
            passed   (list[dict]) — contrôles conformes.
            summary  (dict)       — total_checks, passed, failed.
    """
    findings = []
    passed = []

    for fn in [_r58_unnecessary_packages, _r59_trusted_repos, _r61_security_updates]:
        f, p = fn(ssh)
        findings.extend(f)
        passed.extend(p)

    return {
        "findings": findings,
        "passed": passed,
        "summary": {
            "total_checks": len(findings) + len(passed),
            "passed": len(passed),
            "failed": len(findings),
        },
    }
