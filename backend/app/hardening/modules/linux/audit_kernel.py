# Module d'audit : paramètres noyau Linux
# Référentiel : ANSSI-BP-028 v2.0 — Sections 5.2 (configuration dynamique)
# Checks : R8 (mémoire), R9 (modules), R10 (Yama), R11 (IPv6), R12 (IPv4), R13 (FS), R14 (processus)

# Chaque tuple : (sysctl_param, valeur_attendue, sévérité, check_id, ref_anssi, description, remédiation)
SYSCTL_CHECKS = [
    # ── R8 : Configuration de la mémoire ──────────────────────────────────────
    ("kernel.randomize_va_space",           "2",   "HIGH",   "KERNEL-R8-001", "R8",
     "ASLR complet activé (randomise l'espace d'adressage, protège contre les exploits)",
     "echo 'kernel.randomize_va_space = 2' >> /etc/sysctl.d/99-anssi.conf && sysctl -p /etc/sysctl.d/99-anssi.conf"),

    ("vm.mmap_min_addr",                    "65536","MEDIUM", "KERNEL-R8-002", "R8",
     "Adresse mémoire minimale pour les mappings (évite les null pointer dereference)",
     "echo 'vm.mmap_min_addr = 65536' >> /etc/sysctl.d/99-anssi.conf && sysctl -p /etc/sysctl.d/99-anssi.conf"),

    # ── R9 : Configuration du noyau ───────────────────────────────────────────
    ("kernel.dmesg_restrict",               "1",   "MEDIUM", "KERNEL-R9-001", "R9",
     "Accès à dmesg restreint aux root (empêche la fuite d'infos noyau)",
     "echo 'kernel.dmesg_restrict = 1' >> /etc/sysctl.d/99-anssi.conf"),

    ("kernel.kptr_restrict",                "2",   "MEDIUM", "KERNEL-R9-002", "R9",
     "Pointeurs noyau masqués pour tous (prévient la fuite d'adresses kernel)",
     "echo 'kernel.kptr_restrict = 2' >> /etc/sysctl.d/99-anssi.conf"),

    ("kernel.perf_event_paranoid",          "3",   "LOW",    "KERNEL-R9-003", "R9",
     "perf_events restreint (réduit la fuite d'infos sur les performances CPU)",
     "echo 'kernel.perf_event_paranoid = 3' >> /etc/sysctl.d/99-anssi.conf"),

    ("kernel.unprivileged_bpf_disabled",    "1",   "HIGH",   "KERNEL-R9-004", "R9",
     "eBPF restreint aux root (vecteur d'exploitation kernel sans ce paramètre)",
     "echo 'kernel.unprivileged_bpf_disabled = 1' >> /etc/sysctl.d/99-anssi.conf"),

    ("net.core.bpf_jit_harden",            "2",   "MEDIUM", "KERNEL-R9-005", "R9",
     "BPF JIT durci contre les spraying attacks",
     "echo 'net.core.bpf_jit_harden = 2' >> /etc/sysctl.d/99-anssi.conf"),

    # ── R10 : LSM Yama — restriction ptrace ───────────────────────────────────
    ("kernel.yama.ptrace_scope",            "1",   "HIGH",   "KERNEL-R10-001", "R10",
     "Yama LSM : ptrace limité au parent (empêche l'inspection de processus tiers)",
     "echo 'kernel.yama.ptrace_scope = 1' >> /etc/sysctl.d/99-anssi.conf"),

    # ── R12 : Configuration réseau IPv4 ───────────────────────────────────────
    ("net.ipv4.ip_forward",                 "0",   "HIGH",   "KERNEL-R12-001", "R12",
     "IP forwarding désactivé (pas de routage entre interfaces)",
     "echo 'net.ipv4.ip_forward = 0' >> /etc/sysctl.d/99-anssi.conf"),

    ("net.ipv4.tcp_syncookies",             "1",   "MEDIUM", "KERNEL-R12-002", "R12",
     "SYN Cookies activé (protection contre les attaques SYN flood)",
     "echo 'net.ipv4.tcp_syncookies = 1' >> /etc/sysctl.d/99-anssi.conf"),

    ("net.ipv4.conf.all.accept_redirects",  "0",   "MEDIUM", "KERNEL-R12-003", "R12",
     "Redirects ICMP refusés sur toutes les interfaces (protection contre le MITM)",
     "echo 'net.ipv4.conf.all.accept_redirects = 0' >> /etc/sysctl.d/99-anssi.conf"),

    ("net.ipv4.conf.default.accept_redirects","0", "MEDIUM", "KERNEL-R12-004", "R12",
     "Redirects ICMP refusés par défaut (protection contre le MITM)",
     "echo 'net.ipv4.conf.default.accept_redirects = 0' >> /etc/sysctl.d/99-anssi.conf"),

    ("net.ipv4.conf.all.accept_source_route","0",  "HIGH",   "KERNEL-R12-005", "R12",
     "Source routing désactivé (prévient l'usurpation d'adresse IP)",
     "echo 'net.ipv4.conf.all.accept_source_route = 0' >> /etc/sysctl.d/99-anssi.conf"),

    ("net.ipv4.conf.all.send_redirects",    "0",   "MEDIUM", "KERNEL-R12-006", "R12",
     "Envoi de redirects ICMP désactivé (pas de routeur sur cette machine)",
     "echo 'net.ipv4.conf.all.send_redirects = 0' >> /etc/sysctl.d/99-anssi.conf"),

    ("net.ipv4.conf.all.log_martians",      "1",   "LOW",    "KERNEL-R12-007", "R12",
     "Log des paquets à adresse source invalide (détection d'usurpation IP)",
     "echo 'net.ipv4.conf.all.log_martians = 1' >> /etc/sysctl.d/99-anssi.conf"),

    ("net.ipv4.icmp_echo_ignore_broadcasts","1",   "LOW",    "KERNEL-R12-008", "R12",
     "Ignore les pings broadcast (prévient les attaques Smurf)",
     "echo 'net.ipv4.icmp_echo_ignore_broadcasts = 1' >> /etc/sysctl.d/99-anssi.conf"),

    ("net.ipv4.icmp_ignore_bogus_error_responses","1","LOW", "KERNEL-R12-009", "R12",
     "Ignore les réponses ICMP invalides (réduit le bruit réseau malveillant)",
     "echo 'net.ipv4.icmp_ignore_bogus_error_responses = 1' >> /etc/sysctl.d/99-anssi.conf"),

    ("net.ipv4.conf.all.rp_filter",         "1",   "MEDIUM", "KERNEL-R12-010", "R12",
     "Reverse path filtering activé (anti-spoofing IP)",
     "echo 'net.ipv4.conf.all.rp_filter = 1' >> /etc/sysctl.d/99-anssi.conf"),

    ("net.ipv4.tcp_rfc1337",                "1",   "LOW",    "KERNEL-R12-011", "R12",
     "Protection TIME_WAIT assassination (RFC 1337)",
     "echo 'net.ipv4.tcp_rfc1337 = 1' >> /etc/sysctl.d/99-anssi.conf"),

    # ── R13 : Systèmes de fichiers ─────────────────────────────────────────────
    ("fs.suid_dumpable",                    "0",   "HIGH",   "KERNEL-R13-001", "R13",
     "Core dumps des setuid désactivés (évite la fuite de données root dans les dumps)",
     "echo 'fs.suid_dumpable = 0' >> /etc/sysctl.d/99-anssi.conf"),

    ("fs.protected_hardlinks",              "1",   "HIGH",   "KERNEL-R13-002", "R13",
     "Liens physiques protégés (empêche les attaques via hardlinks vers fichiers sensibles)",
     "echo 'fs.protected_hardlinks = 1' >> /etc/sysctl.d/99-anssi.conf"),

    ("fs.protected_symlinks",               "1",   "HIGH",   "KERNEL-R13-003", "R13",
     "Liens symboliques protégés dans les sticky dirs (empêche les attaques par symlink)",
     "echo 'fs.protected_symlinks = 1' >> /etc/sysctl.d/99-anssi.conf"),

    ("fs.protected_fifos",                  "2",   "MEDIUM", "KERNEL-R13-004", "R13",
     "FIFO protégées dans les sticky dirs (évite les substitutions de fichiers de logs)",
     "echo 'fs.protected_fifos = 2' >> /etc/sysctl.d/99-anssi.conf"),
]


def _check_modules_disabled(ssh):
    """R9 — Vérifier si le chargement de modules noyau est désactivé."""
    out, _ = ssh.execute_command("sysctl -n kernel.modules_disabled 2>/dev/null")
    val = out.strip()
    if val == "1":
        return None, {"check": "KERNEL-R9-MOD", "check_name": "kernel.modules_disabled",
                      "found": "modules_disabled=1 (durcissement maximal)"}
    return {
        "check": "KERNEL-R9-MOD",
        "check_name": "kernel.modules_disabled",
        "description": "Chargement de modules noyau non verrouillé (R9 — niveau renforcé)",
        "found": val or "non défini",
        "expected": "1",
        "severity": "LOW",
        "remediation": "echo 'kernel.modules_disabled = 1' >> /etc/sysctl.d/99-anssi.conf (irréversible sans reboot)",
    }, None


def _check_ipv6_disabled(ssh):
    """R11 — Vérifier si IPv6 est désactivé (si non utilisé)."""
    out, _ = ssh.execute_command("sysctl -n net.ipv6.conf.all.disable_ipv6 2>/dev/null")
    val = out.strip()
    # Informationnel uniquement — IPv6 peut être légitime
    if val == "1":
        return None, {"check": "KERNEL-R11-001", "check_name": "IPv6 désactivé",
                      "found": "IPv6 désactivé (conforme R11 si inutilisé)"}
    return None, {"check": "KERNEL-R11-001", "check_name": "IPv6 activé",
                  "found": "IPv6 actif — vérifier si nécessaire (R11 recommande de désactiver si inutilisé)"}


def run_audit(ssh, rules):
    findings = []
    passed = []

    # Checks sysctl
    for (param, expected, severity, check_id, ref, description, remediation) in SYSCTL_CHECKS:
        out, _ = ssh.execute_command(f"sysctl -n {param} 2>/dev/null")
        found = out.strip()

        if not found:
            findings.append({
                "check": check_id,
                "check_name": param,
                "description": f"[ANSSI {ref}] {description}",
                "found": "paramètre absent",
                "expected": expected,
                "severity": severity,
                "remediation": remediation,
            })
        elif found != expected:
            findings.append({
                "check": check_id,
                "check_name": param,
                "description": f"[ANSSI {ref}] {description}",
                "found": found,
                "expected": expected,
                "severity": severity,
                "remediation": remediation,
            })
        else:
            passed.append({
                "check": check_id,
                "check_name": param,
                "description": f"[ANSSI {ref}] {description}",
                "found": found,
            })

    # R9 — Modules chargement
    f, p = _check_modules_disabled(ssh)
    if f:
        findings.append(f)
    if p:
        passed.append(p)

    # R11 — IPv6 (informatif)
    _, p = _check_ipv6_disabled(ssh)
    if p:
        passed.append(p)

    return {
        "findings": findings,
        "passed": passed,
        "summary": {
            "total_checks": len(findings) + len(passed),
            "passed": len(passed),
            "failed": len(findings),
        },
    }
