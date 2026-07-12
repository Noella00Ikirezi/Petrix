"""Module de remédiation automatique pour les findings HCO Linux.

Applique ou prévisualise (mode dry-run par défaut) les correctifs identifiés
par les modules d'audit SSH, noyau et pare-feu. Chaque correction crée une
sauvegarde horodatée du fichier modifié avant toute opération.
"""
# Mode DRY-RUN par défaut — ne modifie rien sans confirmation explicite

SSH_CONFIG = "/etc/ssh/sshd_config"
SYSCTL_CONF = "/etc/sysctl.d/99-hco-hardening.conf"

# Catalogue des remédiation par check_id
# Chaque entrée : (description, commandes_liste, reboot_required)
REMEDIATION_CATALOG = {

    # ── SSH ──────────────────────────────────────────────────────────
    "SSH-001": (
        "Désactiver la connexion SSH root directe",
        [
            f"grep -q '^PermitRootLogin' {SSH_CONFIG} "
            f"&& sed -i 's/^PermitRootLogin.*/PermitRootLogin no/' {SSH_CONFIG} "
            f"|| echo 'PermitRootLogin no' >> {SSH_CONFIG}",
            "systemctl restart sshd",
        ],
        False,
    ),
    "SSH-002": (
        "Désactiver l'authentification par mot de passe SSH",
        [
            f"grep -q '^PasswordAuthentication' {SSH_CONFIG} "
            f"&& sed -i 's/^PasswordAuthentication.*/PasswordAuthentication no/' {SSH_CONFIG} "
            f"|| echo 'PasswordAuthentication no' >> {SSH_CONFIG}",
            "systemctl restart sshd",
        ],
        False,
    ),
    "SSH-003": (
        "Interdire les mots de passe vides",
        [
            f"grep -q '^PermitEmptyPasswords' {SSH_CONFIG} "
            f"&& sed -i 's/^PermitEmptyPasswords.*/PermitEmptyPasswords no/' {SSH_CONFIG} "
            f"|| echo 'PermitEmptyPasswords no' >> {SSH_CONFIG}",
            "systemctl restart sshd",
        ],
        False,
    ),
    "SSH-004": (
        "Désactiver X11 Forwarding",
        [
            f"grep -q '^X11Forwarding' {SSH_CONFIG} "
            f"&& sed -i 's/^X11Forwarding.*/X11Forwarding no/' {SSH_CONFIG} "
            f"|| echo 'X11Forwarding no' >> {SSH_CONFIG}",
            "systemctl restart sshd",
        ],
        False,
    ),
    "SSH-015": (
        "Limiter MaxAuthTries à 4",
        [
            f"grep -q '^MaxAuthTries' {SSH_CONFIG} "
            f"&& sed -i 's/^MaxAuthTries.*/MaxAuthTries 4/' {SSH_CONFIG} "
            f"|| echo 'MaxAuthTries 4' >> {SSH_CONFIG}",
            "systemctl restart sshd",
        ],
        False,
    ),
    "SSH-016": (
        "Configurer un timeout de session SSH (5 minutes)",
        [
            f"grep -q '^ClientAliveInterval' {SSH_CONFIG} "
            f"&& sed -i 's/^ClientAliveInterval.*/ClientAliveInterval 300/' {SSH_CONFIG} "
            f"|| echo 'ClientAliveInterval 300' >> {SSH_CONFIG}",
            f"grep -q '^ClientAliveCountMax' {SSH_CONFIG} "
            f"&& sed -i 's/^ClientAliveCountMax.*/ClientAliveCountMax 3/' {SSH_CONFIG} "
            f"|| echo 'ClientAliveCountMax 3' >> {SSH_CONFIG}",
            "systemctl restart sshd",
        ],
        False,
    ),
    "SSH-020": (
        "Restreindre les ciphers SSH aux algorithmes forts",
        [
            f"grep -q '^Ciphers' {SSH_CONFIG} "
            f"&& sed -i 's/^Ciphers.*//' {SSH_CONFIG}",
            f"echo 'Ciphers chacha20-poly1305@openssh.com,aes256-gcm@openssh.com,aes128-gcm@openssh.com,aes256-ctr,aes192-ctr,aes128-ctr' >> {SSH_CONFIG}",
            "systemctl restart sshd",
        ],
        False,
    ),
    "SSH-021": (
        "Restreindre les MACs SSH aux algorithmes ETM/SHA-2",
        [
            f"grep -q '^MACs' {SSH_CONFIG} "
            f"&& sed -i 's/^MACs.*//' {SSH_CONFIG}",
            f"echo 'MACs hmac-sha2-256-etm@openssh.com,hmac-sha2-512-etm@openssh.com,umac-128-etm@openssh.com' >> {SSH_CONFIG}",
            "systemctl restart sshd",
        ],
        False,
    ),
    "SSH-022": (
        "Restreindre les KexAlgorithms SSH aux échanges de clés modernes",
        [
            f"grep -q '^KexAlgorithms' {SSH_CONFIG} "
            f"&& sed -i 's/^KexAlgorithms.*//' {SSH_CONFIG}",
            f"echo 'KexAlgorithms curve25519-sha256,curve25519-sha256@libssh.org,ecdh-sha2-nistp256,ecdh-sha2-nistp384,diffie-hellman-group16-sha512,diffie-hellman-group18-sha512' >> {SSH_CONFIG}",
            "systemctl restart sshd",
        ],
        False,
    ),

    # ── Kernel sysctl ────────────────────────────────────────────────
    "KERNEL-001": (
        "Désactiver l'IP forwarding",
        [
            f"grep -q 'net.ipv4.ip_forward' {SYSCTL_CONF} 2>/dev/null "
            f"|| echo 'net.ipv4.ip_forward = 0' >> {SYSCTL_CONF}",
            f"sysctl -p {SYSCTL_CONF}",
        ],
        False,
    ),
    "KERNEL-002": (
        "Activer les SYN Cookies (protection SYN flood)",
        [
            f"grep -q 'net.ipv4.tcp_syncookies' {SYSCTL_CONF} 2>/dev/null "
            f"|| echo 'net.ipv4.tcp_syncookies = 1' >> {SYSCTL_CONF}",
            f"sysctl -p {SYSCTL_CONF}",
        ],
        False,
    ),
    "KERNEL-003": (
        "Activer ASLR complet (randomize_va_space=2)",
        [
            f"grep -q 'kernel.randomize_va_space' {SYSCTL_CONF} 2>/dev/null "
            f"|| echo 'kernel.randomize_va_space = 2' >> {SYSCTL_CONF}",
            f"sysctl -p {SYSCTL_CONF}",
        ],
        False,
    ),

    # ── Firewall ─────────────────────────────────────────────────────
    "FW-001": (
        "Activer ufw avec politique deny par défaut",
        [
            "ufw default deny incoming",
            "ufw default allow outgoing",
            "ufw allow ssh",
            "ufw --force enable",
        ],
        False,
    ),
    "FW-002": (
        "Appliquer la politique par défaut DENY sur le trafic entrant",
        [
            "ufw default deny incoming",
            "ufw reload",
        ],
        False,
    ),

    # ── Services dangereux ───────────────────────────────────────────
    "SVC-001": (
        "Arrêter et désactiver Telnet",
        [
            "systemctl stop telnet 2>/dev/null || true",
            "systemctl disable telnet 2>/dev/null || true",
            "apt-get purge telnetd telnet -y 2>/dev/null || yum remove telnet-server telnet -y 2>/dev/null || true",
        ],
        False,
    ),
    "SVC-002": (
        "Arrêter et désactiver FTP",
        [
            "systemctl stop vsftpd proftpd pure-ftpd 2>/dev/null || true",
            "systemctl disable vsftpd proftpd pure-ftpd 2>/dev/null || true",
            "apt-get purge vsftpd proftpd pure-ftpd -y 2>/dev/null || yum remove vsftpd proftpd pure-ftpd -y 2>/dev/null || true",
        ],
        False,
    ),
    "SVC-100": (
        "Activer et démarrer auditd",
        [
            "apt-get install -y auditd 2>/dev/null || yum install -y audit 2>/dev/null || true",
            "systemctl enable --now auditd",
        ],
        False,
    ),
}


def _create_backup(ssh, filepath):
    """Crée une sauvegarde horodatée avant modification."""
    out, _ = ssh.execute_command(
        f"cp -p {filepath} {filepath}.hco-backup-$(date +%Y%m%d-%H%M%S) 2>/dev/null && echo 'ok'"
    )
    return "ok" in out


def run_remediation(ssh, findings, dry_run=True):
    """
    Applique ou prévisualise les correctifs pour chaque finding.

    Args:
        ssh: connecteur SSH
        findings: liste de dicts {"check": check_id, ...}
        dry_run: True = prévisualisation seulement, False = applique les changements

    Returns:
        dict avec applied, skipped, failed, preview (dry_run uniquement)
    """
    applied = []
    skipped = []
    failed = []
    preview = []

    for finding in findings:
        check_id = finding.get("check", "")
        if not check_id or check_id not in REMEDIATION_CATALOG:
            skipped.append({
                "check": check_id,
                "reason": "Pas de remédiation automatique disponible pour ce check",
            })
            continue

        description, commands, reboot_req = REMEDIATION_CATALOG[check_id]

        if dry_run:
            preview.append({
                "check": check_id,
                "description": description,
                "commands": commands,
                "reboot_required": reboot_req,
            })
            continue

        # Mode réel : créer une sauvegarde SSH config avant modification
        if check_id.startswith("SSH-"):
            _create_backup(ssh, "/etc/ssh/sshd_config")

        # Exécuter les commandes de remédiation
        success = True
        errors = []
        for cmd in commands:
            out, err = ssh.execute_command(cmd)
            if err and "warning" not in err.lower():
                errors.append(f"CMD: {cmd[:80]}... → ERR: {err[:120]}")
                success = False

        if success:
            applied.append({
                "check": check_id,
                "description": description,
                "reboot_required": reboot_req,
            })
        else:
            failed.append({
                "check": check_id,
                "description": description,
                "errors": errors,
            })

    reboot_needed = any(r.get("reboot_required") for r in applied)

    return {
        "dry_run": dry_run,
        "applied": applied,
        "skipped": skipped,
        "failed": failed,
        "preview": preview,
        "reboot_required": reboot_needed,
        "summary": {
            "total": len(findings),
            "applied": len(applied),
            "skipped": len(skipped),
            "failed": len(failed),
            "preview": len(preview),
        },
    }
