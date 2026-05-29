# Module d'audit : vérifie les paramètres sysctl de sécurité du noyau Linux
# Référentiel : CIS Benchmark Linux v2.0 — Section 3 (Network Parameters) + Section 1.6 (Mandatory Access Control)

SYSCTL_CHECKS = [
    # (paramètre, valeur_attendue, sévérité, check_id, description)
    ("net.ipv4.ip_forward",                   "0", "HIGH",   "KERNEL-001", "IP forwarding désactivé (pas de routage)"),
    ("net.ipv4.tcp_syncookies",               "1", "MEDIUM", "KERNEL-002", "SYN Cookies activé (protection SYN flood)"),
    ("kernel.randomize_va_space",             "2", "HIGH",   "KERNEL-003", "ASLR complet activé (protection exploit)"),
    ("net.ipv4.conf.all.accept_redirects",    "0", "MEDIUM", "KERNEL-004", "Redirects ICMP refusés (toutes interfaces)"),
    ("net.ipv4.conf.default.accept_redirects","0", "MEDIUM", "KERNEL-005", "Redirects ICMP refusés (interfaces par défaut)"),
    ("net.ipv4.conf.all.accept_source_route", "0", "HIGH",   "KERNEL-006", "Source routing désactivé (usurpation IP)"),
    ("net.ipv4.conf.all.log_martians",        "1", "LOW",    "KERNEL-007", "Log des paquets suspects activé"),
    ("net.ipv4.conf.all.send_redirects",      "0", "MEDIUM", "KERNEL-008", "Envoi de redirects ICMP désactivé"),
    ("net.ipv4.icmp_echo_ignore_broadcasts",  "1", "LOW",    "KERNEL-009", "Ignore les pings broadcast (Smurf attack)"),
    ("net.ipv4.icmp_ignore_bogus_error_responses", "1", "LOW", "KERNEL-010", "Ignore les réponses ICMP invalides"),
    ("kernel.dmesg_restrict",                 "1", "MEDIUM", "KERNEL-011", "dmesg restreint aux root (fuite d'info kernel)"),
    ("kernel.kptr_restrict",                  "2", "MEDIUM", "KERNEL-012", "Pointeurs kernel masqués (kptr_restrict=2)"),
    ("net.ipv4.conf.all.rp_filter",           "1", "MEDIUM", "KERNEL-013", "Reverse path filtering activé (anti-spoofing)"),
    ("kernel.perf_event_paranoid",            "3", "LOW",    "KERNEL-014", "perf_events restreint (fuite info CPU)"),
]


def run_audit(ssh, rules):
    findings = []
    passed = []

    for param, expected, severity, check_id, description in SYSCTL_CHECKS:
        out, err = ssh.execute_command(f"sysctl -n {param} 2>/dev/null")
        found = out.strip()

        if not found:
            findings.append({
                "check": check_id,
                "check_name": param,
                "description": description,
                "found": "non défini",
                "expected": expected,
                "severity": severity,
                "remediation": f"echo '{param} = {expected}' >> /etc/sysctl.d/99-hco.conf && sysctl -p /etc/sysctl.d/99-hco.conf",
            })
        elif found != expected:
            findings.append({
                "check": check_id,
                "check_name": param,
                "description": description,
                "found": found,
                "expected": expected,
                "severity": severity,
                "remediation": f"echo '{param} = {expected}' >> /etc/sysctl.d/99-hco.conf && sysctl -p /etc/sysctl.d/99-hco.conf",
            })
        else:
            passed.append({
                "check": check_id,
                "check_name": param,
                "description": description,
                "found": found,
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
