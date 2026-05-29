# Module d'audit : analyse les ports en écoute et détecte les expositions réseau inattendues
# Référentiel : CIS Benchmark Linux v2.0 — Section 2.2 + bonnes pratiques réseau

# Ports toujours légitimes sur un serveur (whitelist de base)
KNOWN_LEGITIMATE_PORTS = {
    "22":   "SSH",
    "80":   "HTTP",
    "443":  "HTTPS",
    "25":   "SMTP",
    "587":  "SMTP submission",
    "993":  "IMAPS",
    "465":  "SMTPS",
    "53":   "DNS",
    "123":  "NTP",
    "3306": "MySQL",
    "5432": "PostgreSQL",
    "6379": "Redis",
    "27017":"MongoDB",
    "8080": "HTTP alternatif",
    "8443": "HTTPS alternatif",
}

# Ports critiques qui ne devraient JAMAIS être exposés publiquement
HIGH_RISK_PORTS = {
    "21":   ("FTP", "CRITICAL", "Transmission en clair des credentials"),
    "23":   ("Telnet", "CRITICAL", "Session non chiffrée"),
    "69":   ("TFTP", "HIGH",     "Transfert sans authentification"),
    "111":  ("rpcbind", "MEDIUM", "Exposition du portmapper RPC"),
    "135":  ("MS-RPC", "HIGH",    "Vecteur d'exploitation Windows"),
    "139":  ("NetBIOS", "HIGH",   "Protocole obsolète, surface d'attaque"),
    "445":  ("SMB", "HIGH",       "EternalBlue, WannaCry — à filtrer"),
    "512":  ("rexec", "CRITICAL", "Exécution distante non chiffrée"),
    "513":  ("rlogin", "CRITICAL","Connexion distante non chiffrée"),
    "514":  ("rsh/syslog", "HIGH","rsh non chiffré ou syslog exposé"),
    "1099": ("Java RMI", "HIGH",  "Souvent exploité pour RCE"),
    "2049": ("NFS", "HIGH",       "NFS exposé — vérifier les exports"),
    "3389": ("RDP", "HIGH",       "RDP exposé — vecteur de bruteforce"),
    "4444": ("Metasploit", "CRITICAL", "Port Metasploit par défaut — potentiel backdoor"),
    "5900": ("VNC", "HIGH",       "VNC souvent sans auth ou faible"),
    "6000": ("X11", "HIGH",       "X11 exposé — capture écran/clavier"),
    "8080": ("HTTP proxy", "LOW", "Vérifier si intentionnel"),
    "9200": ("Elasticsearch", "HIGH", "Elasticsearch sans auth par défaut"),
    "27017":("MongoDB", "HIGH",   "MongoDB sans auth par défaut"),
}


def _parse_ss_output(output):
    """Parse la sortie de `ss -tlnp` ou `ss -tulnp` en liste de dicts."""
    ports = []
    for line in output.strip().splitlines():
        parts = line.split()
        if len(parts) < 5:
            continue
        # Format: State Recv-Q Send-Q Local-Address:Port Peer-Address:Port [Process]
        local = parts[3] if len(parts) > 3 else ""
        process = " ".join(parts[6:]) if len(parts) > 6 else ""

        # Extraire le port du format addr:port ou [::]:port ou *:port
        if ":" in local:
            port = local.rsplit(":", 1)[-1]
            addr = local.rsplit(":", 1)[0]
        else:
            continue

        ports.append({"port": port, "addr": addr, "process": process, "raw": line})
    return ports


def run_audit(ssh, rules):
    findings = []
    passed = []
    allowed_ports = set(rules.get("allowed_ports", KNOWN_LEGITIMATE_PORTS.keys()))

    # --- Récupérer les ports en écoute (TCP + UDP) ---
    out_ss, err_ss = ssh.execute_command("ss -tulnp 2>/dev/null")
    if not out_ss.strip():
        # Fallback netstat
        out_ss, _ = ssh.execute_command("netstat -tulnp 2>/dev/null")

    parsed_ports = _parse_ss_output(out_ss)

    # Filtrer les lignes header
    parsed_ports = [p for p in parsed_ports if p["port"].isdigit()]

    # Ports uniques en écoute
    listening_ports = {p["port"] for p in parsed_ports}

    # --- Check 1 : ports à risque élevé exposés ---
    for port, (service, severity, reason) in HIGH_RISK_PORTS.items():
        if port in listening_ports:
            process_info = next((p["process"] for p in parsed_ports if p["port"] == port), "")
            findings.append({
                "check": f"NET-{port}",
                "check_name": f"port:{port}/{service}",
                "description": f"Port {port} ({service}) ouvert — {reason}",
                "found": f"port {port} ouvert" + (f" [{process_info}]" if process_info else ""),
                "expected": "fermé ou filtré",
                "severity": severity,
                "remediation": f"Désactiver le service associé ou filtrer avec : ufw deny {port}",
            })
        else:
            passed.append({
                "check": f"NET-{port}",
                "check_name": f"port:{port}/{service}",
                "found": f"port {port} fermé",
            })

    # --- Check 2 : ports inconnus en écoute sur 0.0.0.0 ou :: ---
    unknown_exposed = []
    for p in parsed_ports:
        port = p["port"]
        addr = p["addr"]
        is_public = addr in ("0.0.0.0", "::", "*", "0.0.0.0:*", ":::*")
        is_known = port in KNOWN_LEGITIMATE_PORTS or port in HIGH_RISK_PORTS
        is_allowed = port in allowed_ports

        if is_public and not is_known and not is_allowed:
            unknown_exposed.append(p)

    if unknown_exposed:
        for p in unknown_exposed:
            findings.append({
                "check": "NET-UNKNOWN",
                "check_name": f"port:{p['port']}/unknown",
                "description": f"Port inconnu {p['port']} exposé sur toutes les interfaces",
                "found": f"{p['addr']}:{p['port']} [{p['process']}]",
                "expected": "port documenté ou filtré",
                "severity": "MEDIUM",
                "remediation": f"Identifier le processus sur port {p['port']} : ss -tlnp | grep {p['port']}",
            })
    else:
        passed.append({
            "check": "NET-UNKNOWN",
            "check_name": "ports inconnus exposés",
            "found": "Aucun port inconnu exposé publiquement",
        })

    # --- Check 3 : SSH sur port par défaut (22) exposé à 0.0.0.0 ---
    ssh_entries = [p for p in parsed_ports if p["port"] == "22"]
    for entry in ssh_entries:
        if entry["addr"] in ("0.0.0.0", "::", "*"):
            findings.append({
                "check": "NET-SSH-EXPOSURE",
                "check_name": "SSH exposed on all interfaces",
                "description": "SSH écoute sur toutes les interfaces — recommandé de restreindre à l'IP de management",
                "found": f"SSH sur {entry['addr']}:22",
                "expected": "SSH sur IP de management uniquement",
                "severity": "LOW",
                "remediation": "Dans sshd_config : ListenAddress <IP_management> — ou filtrer via ufw/iptables",
            })

    # --- Résumé des ports en écoute (INFO) ---
    passed.append({
        "check": "NET-INVENTORY",
        "check_name": "inventaire des ports",
        "found": f"{len(listening_ports)} ports en écoute : {', '.join(sorted(listening_ports, key=lambda x: int(x)))}",
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
