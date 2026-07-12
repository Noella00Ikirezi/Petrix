"""Module d'audit du pare-feu Linux (ufw, iptables, firewalld, nftables).

Détecte automatiquement le gestionnaire de pare-feu disponible sur la cible
et vérifie son état d'activation et sa politique par défaut selon le
CIS Benchmark Linux v2.0 § 3.5.
"""
# Référentiel : CIS Benchmark Linux v2.0 — Section 3.5 (Firewall Configuration)

# Services qui doivent toujours être autorisés (ports entrants légitimes)
DEFAULT_ALLOWED_PORTS = {"22", "80", "443"}


def _audit_ufw(ssh, rules):
    """Audit via ufw (Ubuntu/Debian)."""
    findings = []
    passed = []

    out, _ = ssh.execute_command("ufw status 2>/dev/null | head -1")
    status = out.strip().lower()

    if "inactive" in status or not status:
        findings.append({
            "check": "FW-001",
            "check_name": "ufw status",
            "description": "Le pare-feu ufw doit être actif",
            "found": status or "inactif / non installé",
            "expected": "active",
            "severity": "HIGH",
            "remediation": "ufw enable",
        })
    else:
        passed.append({"check": "FW-001", "check_name": "ufw status", "found": status})

        # Politique par défaut INPUT
        out, _ = ssh.execute_command("ufw status verbose 2>/dev/null | grep '^Default:' | head -1")
        if out.strip():
            if "deny (incoming)" not in out.lower() and "drop (incoming)" not in out.lower():
                findings.append({
                    "check": "FW-002",
                    "check_name": "ufw default incoming policy",
                    "description": "La politique par défaut entrante doit être DENY ou DROP",
                    "found": out.strip(),
                    "expected": "deny (incoming)",
                    "severity": "HIGH",
                    "remediation": "ufw default deny incoming",
                })
            else:
                passed.append({"check": "FW-002", "check_name": "ufw default incoming policy", "found": out.strip()})

    return findings, passed


def _audit_iptables(ssh, rules):
    """Audit via iptables."""
    findings = []
    passed = []

    # Vérifier si iptables est disponible et a des règles
    out, err = ssh.execute_command("iptables -L INPUT --line-numbers 2>/dev/null | wc -l")
    try:
        rule_count = int(out.strip())
    except ValueError:
        rule_count = 0

    if rule_count <= 2:
        # Seulement le header, pas de règles réelles
        findings.append({
            "check": "FW-003",
            "check_name": "iptables INPUT rules",
            "description": "Aucune règle iptables INPUT détectée — traffic entrant non filtré",
            "found": f"{max(0, rule_count - 2)} règles actives",
            "expected": ">= 1 règle INPUT",
            "severity": "HIGH",
            "remediation": "Configurer des règles iptables ou activer ufw/firewalld",
        })
    else:
        passed.append({
            "check": "FW-003",
            "check_name": "iptables INPUT rules",
            "found": f"{rule_count - 2} règles actives",
        })

    # Vérifier la politique par défaut INPUT
    out, _ = ssh.execute_command("iptables -L INPUT 2>/dev/null | head -1")
    if out.strip():
        if "ACCEPT" in out and "policy" in out.lower():
            findings.append({
                "check": "FW-004",
                "check_name": "iptables default INPUT policy",
                "description": "La politique par défaut INPUT doit être DROP, pas ACCEPT",
                "found": "policy ACCEPT",
                "expected": "policy DROP",
                "severity": "HIGH",
                "remediation": "iptables -P INPUT DROP",
            })
        else:
            passed.append({"check": "FW-004", "check_name": "iptables default INPUT policy", "found": out.strip()})

    return findings, passed


def _audit_firewalld(ssh, rules):
    """Audit via firewalld (RHEL/CentOS/Fedora)."""
    findings = []
    passed = []

    out, _ = ssh.execute_command("firewall-cmd --state 2>/dev/null")
    if out.strip().lower() != "running":
        findings.append({
            "check": "FW-005",
            "check_name": "firewalld status",
            "description": "firewalld doit être actif",
            "found": out.strip() or "inactif",
            "expected": "running",
            "severity": "HIGH",
            "remediation": "systemctl enable --now firewalld",
        })
    else:
        passed.append({"check": "FW-005", "check_name": "firewalld status", "found": "running"})

    return findings, passed


def run_audit(ssh, rules):
    """Détecte le pare-feu actif et audite son état et sa politique par défaut.

    Tente ufw puis firewalld en priorité ; si aucun des deux n'est trouvé,
    revient sur iptables. Vérifie nftables en complément si présent.

    Args:
        ssh: SSHConnector connecté à la cible.
        rules: dict de règles (non utilisé pour ce module).

    Returns:
        dict avec clés :
            findings (list[dict]) — pare-feu inactif ou politique trop permissive.
            passed   (list[dict]) — contrôles conformes.
            summary  (dict)       — total_checks, passed, failed.
    """
    findings = []
    passed = []
    firewall_found = False

    # Détecter le gestionnaire de pare-feu disponible
    out_ufw, _ = ssh.execute_command("which ufw 2>/dev/null")
    out_firewalld, _ = ssh.execute_command("which firewall-cmd 2>/dev/null")
    out_nft, _ = ssh.execute_command("which nft 2>/dev/null")

    if out_ufw.strip():
        f, p = _audit_ufw(ssh, rules)
        findings.extend(f)
        passed.extend(p)
        firewall_found = True

    if out_firewalld.strip():
        f, p = _audit_firewalld(ssh, rules)
        findings.extend(f)
        passed.extend(p)
        firewall_found = True

    if not firewall_found:
        # Fallback sur iptables
        f, p = _audit_iptables(ssh, rules)
        findings.extend(f)
        passed.extend(p)

    # Vérification nftables (moderne, remplace iptables sur Debian 12+)
    if out_nft.strip():
        out, _ = ssh.execute_command("nft list ruleset 2>/dev/null | wc -l")
        try:
            nft_lines = int(out.strip())
        except ValueError:
            nft_lines = 0

        if nft_lines > 5:
            passed.append({"check": "FW-006", "check_name": "nftables ruleset", "found": f"{nft_lines} lignes de règles"})
        else:
            findings.append({
                "check": "FW-006",
                "check_name": "nftables ruleset",
                "description": "nftables présent mais aucune règle détectée",
                "found": f"{nft_lines} lignes",
                "expected": "ruleset non vide",
                "severity": "MEDIUM",
                "remediation": "Configurer des règles nftables",
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
