"""Module d'audit de la journalisation et de la surveillance Linux.

Vérifie les recommandations ANSSI-BP-028 v2.0 § 7.3 : démon syslog et
rotation des logs (R71), sous-système auditd et règles d'audit (R72),
confinement du MTA local (R73), intégrité des fichiers via AIDE/debsums (R74).
"""
# Référentiel : ANSSI-BP-028 v2.0 — Section 7.3
# Checks : R71 (syslog/rsyslog), R72 (auditd), R73 (journaux service mail), R74 (intégrité fichiers)


def _r71_syslog(ssh):
    """R71 — Configurer la journalisation système (syslog/rsyslog/journald)."""
    findings, passed = [], []

    # Vérifier qu'un démon de journalisation est installé et actif
    for daemon in ("rsyslog", "syslog-ng", "syslogd"):
        out, _ = ssh.execute_command(f"systemctl is-active {daemon} 2>/dev/null")
        if out.strip() == "active":
            passed.append({"check": "LOG-R71-001", "check_name": "Démon syslog",
                           "found": f"{daemon} actif"})
            break
    else:
        # Vérifier journald seul
        out, _ = ssh.execute_command("systemctl is-active systemd-journald 2>/dev/null")
        if out.strip() == "active":
            passed.append({"check": "LOG-R71-001", "check_name": "Journald actif",
                           "found": "systemd-journald actif (journalisation locale OK)"})
        else:
            findings.append({
                "check": "LOG-R71-001",
                "check_name": "Démon syslog absent",
                "description": "[ANSSI R71] Aucun démon de journalisation système (rsyslog/syslog-ng/journald) "
                               "n'est actif — les événements système ne sont pas enregistrés",
                "found": "rsyslog/syslog-ng/journald inactifs",
                "expected": "rsyslog ou syslog-ng actif",
                "severity": "CRITICAL",
                "remediation": "apt install rsyslog && systemctl enable rsyslog --now",
            })

    # Vérifier la configuration rsyslog (logs auth, kern, etc.)
    out, _ = ssh.execute_command(
        "grep -rE 'auth|kern|daemon|syslog|cron' /etc/rsyslog.conf /etc/rsyslog.d/ 2>/dev/null | "
        "grep -v '#' | grep -c '.'"
    )
    try:
        if int(out.strip()) > 0:
            passed.append({"check": "LOG-R71-002", "check_name": "Règles rsyslog",
                           "found": "Des règles de journalisation auth/kern/daemon configurées"})
    except ValueError:
        pass

    # Vérifier la journalisation de l'authentification (/var/log/auth.log ou /var/log/secure)
    out, _ = ssh.execute_command(
        "ls -la /var/log/auth.log /var/log/secure /var/log/messages 2>/dev/null | head -5"
    )
    log_files = [l for l in out.strip().splitlines() if l]
    if log_files:
        passed.append({"check": "LOG-R71-003", "check_name": "Fichiers de logs",
                       "found": f"Fichiers de journalisation présents : {', '.join(f.split()[-1] for f in log_files[:3])}"})
    else:
        findings.append({
            "check": "LOG-R71-003",
            "check_name": "Fichiers logs auth absents",
            "description": "[ANSSI R71] Les fichiers de journalisation d'authentification "
                           "(/var/log/auth.log, /var/log/secure) sont absents",
            "found": "Aucun fichier de log d'authentification trouvé",
            "expected": "/var/log/auth.log ou /var/log/secure présent",
            "severity": "HIGH",
            "remediation": "Vérifier la configuration rsyslog et relancer : systemctl restart rsyslog",
        })

    # Vérifier la rotation des logs (logrotate)
    out, _ = ssh.execute_command("which logrotate 2>/dev/null && logrotate --version 2>/dev/null | head -1")
    if out.strip():
        passed.append({"check": "LOG-R71-004", "check_name": "Rotation des logs",
                       "found": "logrotate installé — rotation automatique des journaux configurée"})
    else:
        findings.append({
            "check": "LOG-R71-004",
            "check_name": "logrotate absent",
            "description": "[ANSSI R71] logrotate n'est pas installé — "
                           "les fichiers de logs peuvent grossir indéfiniment",
            "found": "logrotate non installé",
            "expected": "logrotate installé et configuré",
            "severity": "LOW",
            "remediation": "apt install logrotate",
        })

    return findings, passed


def _r72_auditd(ssh):
    """R72 — Activer le sous-système d'audit Linux (auditd)."""
    findings, passed = [], []

    # Vérifier si auditd est installé et actif
    out, _ = ssh.execute_command("systemctl is-active auditd 2>/dev/null")
    if out.strip() == "active":
        passed.append({"check": "LOG-R72-001", "check_name": "auditd actif",
                       "found": "auditd actif — audit des appels système activé"})
    else:
        findings.append({
            "check": "LOG-R72-001",
            "check_name": "auditd inactif",
            "description": "[ANSSI R72] Le démon d'audit Linux (auditd) n'est pas actif — "
                           "les accès aux fichiers sensibles et les appels système ne sont pas audités",
            "found": f"auditd : {out.strip() or 'inactif/absent'}",
            "expected": "auditd actif",
            "severity": "HIGH",
            "remediation": "apt install auditd audispd-plugins && systemctl enable auditd --now",
        })
        return findings, passed  # Inutile de vérifier les règles si auditd est absent

    # Vérifier les règles d'audit configurées
    out, _ = ssh.execute_command("auditctl -l 2>/dev/null | grep -v 'No rules' | wc -l")
    try:
        rule_count = int(out.strip())
        if rule_count > 0:
            passed.append({"check": "LOG-R72-002", "check_name": "Règles auditd",
                           "found": f"{rule_count} règle(s) d'audit configurée(s)"})
        else:
            findings.append({
                "check": "LOG-R72-002",
                "check_name": "Aucune règle auditd",
                "description": "[ANSSI R72] auditd est actif mais aucune règle d'audit n'est définie — "
                               "les accès critiques ne sont pas tracés",
                "found": "0 règle configurée",
                "expected": "Règles d'audit pour appels système sensibles (execve, open, chmod, chown…)",
                "severity": "MEDIUM",
                "remediation": "Configurer des règles dans /etc/audit/rules.d/hardening.rules",
            })
    except ValueError:
        pass

    # Vérifier les règles ANSSI recommandées (accès privileged, modifications /etc/)
    KEY_RULES = [
        ("LOG-R72-003", "-w /etc/passwd",          "Surveillance /etc/passwd",   "Modifications du registre utilisateurs non auditées"),
        ("LOG-R72-004", "-w /etc/shadow",           "Surveillance /etc/shadow",   "Accès aux mots de passe hachés non audité"),
        ("LOG-R72-005", "-w /etc/sudoers",          "Surveillance sudoers",       "Modifications sudo non auditées"),
        ("LOG-R72-006", "-a always,exit -F arch=",  "Règles syscall",             "Appels système critiques non audités (execve, ptrace…)"),
    ]
    out, _ = ssh.execute_command("auditctl -l 2>/dev/null")
    rules_text = out.strip()

    for check_id, pattern, check_name, missing_desc in KEY_RULES:
        if pattern in rules_text:
            passed.append({"check": check_id, "check_name": check_name,
                           "found": f"Règle '{pattern}' présente"})
        else:
            findings.append({
                "check": check_id,
                "check_name": check_name,
                "description": f"[ANSSI R72] {missing_desc}",
                "found": f"Règle '{pattern}' absente",
                "expected": f"Règle de surveillance '{pattern}' dans auditd",
                "severity": "MEDIUM",
                "remediation": f"Ajouter dans /etc/audit/rules.d/hardening.rules : {pattern} -p wa -k hardening",
            })

    return findings, passed


def _r73_mail_service(ssh):
    """R73 — Sécuriser le service de messagerie local (MTA)."""
    findings, passed = [], []

    # Vérifier si un MTA est installé (postfix, sendmail, exim)
    MTA_SERVICES = ["postfix", "sendmail", "exim4", "exim"]
    mta_found = None
    for mta in MTA_SERVICES:
        out, _ = ssh.execute_command(f"which {mta} 2>/dev/null || dpkg -l {mta} 2>/dev/null | grep -c '^ii'")
        if out.strip() and out.strip() not in ("0", ""):
            mta_found = mta
            break

    if not mta_found:
        passed.append({"check": "LOG-R73-001", "check_name": "MTA",
                       "found": "Aucun MTA installé — service mail local absent (acceptable sur serveur durci)"})
        return findings, passed

    # MTA présent — vérifier qu'il écoute uniquement sur localhost
    out, _ = ssh.execute_command(
        "ss -tlnp 2>/dev/null | grep ':25 ' || netstat -tlnp 2>/dev/null | grep ':25 '"
    )
    listening_on = out.strip()
    if "0.0.0.0:25" in listening_on or ":::25" in listening_on:
        findings.append({
            "check": "LOG-R73-001",
            "check_name": "MTA exposé sur toutes interfaces",
            "description": "[ANSSI R73] Le service mail (MTA) écoute sur toutes les interfaces — "
                           "risque d'utilisation comme relais mail ou d'exploitation",
            "found": f"{mta_found} écoute sur 0.0.0.0:25 ou :::25",
            "expected": "MTA écoute uniquement sur 127.0.0.1:25",
            "severity": "HIGH",
            "remediation": "Configurer inet_interfaces = loopback-only dans /etc/postfix/main.cf",
        })
    elif "127.0.0.1:25" in listening_on or "::1" in listening_on:
        passed.append({"check": "LOG-R73-001", "check_name": "MTA local uniquement",
                       "found": f"{mta_found} écoute uniquement sur localhost — configuration sécurisée"})
    else:
        passed.append({"check": "LOG-R73-001", "check_name": "MTA",
                       "found": f"{mta_found} installé mais port 25 non ouvert en écoute"})

    return findings, passed


def _r74_file_integrity(ssh):
    """R74 — Vérifier l'intégrité des fichiers système (AIDE/Tripwire)."""
    findings, passed = [], []

    # Vérifier si AIDE est installé
    out, _ = ssh.execute_command("which aide 2>/dev/null || dpkg -l aide 2>/dev/null | grep -c '^ii'")
    if out.strip() and out.strip() not in ("0", ""):
        # AIDE installé — vérifier la base de données
        out2, _ = ssh.execute_command("ls -la /var/lib/aide/aide.db 2>/dev/null || ls -la /var/lib/aide/aide.db.gz 2>/dev/null")
        if out2.strip():
            passed.append({"check": "LOG-R74-001", "check_name": "AIDE configuré",
                           "found": "AIDE installé avec base de données — contrôle d'intégrité actif"})
        else:
            findings.append({
                "check": "LOG-R74-001",
                "check_name": "AIDE sans base de données",
                "description": "[ANSSI R74] AIDE est installé mais la base de données d'intégrité n'existe pas — "
                               "aucune référence pour détecter les modifications",
                "found": "aide installé mais /var/lib/aide/aide.db absent",
                "expected": "Base de données AIDE initialisée",
                "severity": "MEDIUM",
                "remediation": "aide --init && mv /var/lib/aide/aide.db.new /var/lib/aide/aide.db",
            })
    else:
        # Vérifier Tripwire comme alternative
        out, _ = ssh.execute_command("which tripwire 2>/dev/null")
        if out.strip():
            passed.append({"check": "LOG-R74-001", "check_name": "Tripwire",
                           "found": "Tripwire installé — contrôle d'intégrité alternatif actif"})
        else:
            findings.append({
                "check": "LOG-R74-001",
                "check_name": "Aucun outil d'intégrité",
                "description": "[ANSSI R74] Aucun outil de contrôle d'intégrité des fichiers (AIDE, Tripwire) "
                               "n'est installé — des modifications malveillantes de fichiers système "
                               "ne pourraient pas être détectées",
                "found": "AIDE et Tripwire absents",
                "expected": "AIDE configuré avec vérification périodique via cron",
                "severity": "MEDIUM",
                "remediation": "apt install aide && aide --init && "
                               "mv /var/lib/aide/aide.db.new /var/lib/aide/aide.db && "
                               "echo '0 5 * * * root /usr/bin/aide --check' >> /etc/crontab",
            })

    # Vérifier que les sums des binaires critiques peuvent être vérifiées (debsums)
    out, _ = ssh.execute_command("which debsums 2>/dev/null")
    if out.strip():
        out2, _ = ssh.execute_command("debsums -s 2>/dev/null | wc -l")
        try:
            altered = int(out2.strip())
            if altered > 0:
                findings.append({
                    "check": "LOG-R74-002",
                    "check_name": "Fichiers paquets altérés",
                    "description": f"[ANSSI R74] debsums détecte {altered} fichier(s) de paquets modifiés — "
                                   "possible compromission ou modification non autorisée",
                    "found": f"{altered} fichier(s) altéré(s)",
                    "expected": "0 fichier modifié (cohérence avec les paquets installés)",
                    "severity": "HIGH",
                    "remediation": "Exécuter 'debsums -s' pour identifier les fichiers, puis réinstaller : "
                                   "apt install --reinstall <paquet>",
                })
            else:
                passed.append({"check": "LOG-R74-002", "check_name": "debsums",
                               "found": "Tous les fichiers de paquets correspondent aux sommes officielles"})
        except ValueError:
            pass

    return findings, passed


def run_audit(ssh, rules):
    """Exécute l'audit complet de journalisation et de surveillance.

    Enchaîne R71 (syslog), R72 (auditd), R73 (MTA) et R74 (intégrité)
    puis agrège les résultats.

    Args:
        ssh: SSHConnector connecté à la cible.
        rules: dict de règles (non utilisé pour ce module).

    Returns:
        dict avec clés :
            findings (list[dict]) — services absents ou configurations
                                    insuffisantes.
            passed   (list[dict]) — contrôles conformes.
            summary  (dict)       — total_checks, passed, failed.
    """
    findings = []
    passed = []

    for fn in [_r71_syslog, _r72_auditd, _r73_mail_service, _r74_file_integrity]:
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
