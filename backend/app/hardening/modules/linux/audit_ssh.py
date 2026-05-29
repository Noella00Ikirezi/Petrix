# Module d'audit : configuration SSH complète — Linux
# Référentiel : CIS Benchmark Linux v2.0 Section 5.2 + Mozilla SSH Guidelines (Modern policy)
# https://infosec.mozilla.org/guidelines/openssh

# Ciphers considérés faibles ou cassés (CBC mode vulnérable aux padding oracles)
WEAK_CIPHERS = {
    "3des-cbc", "aes128-cbc", "aes192-cbc", "aes256-cbc",
    "rijndael-cbc@lysator.liu.se", "arcfour", "arcfour128", "arcfour256",
    "blowfish-cbc", "cast128-cbc", "idea-cbc",
}

# Ciphers recommandés (AES-GCM et ChaCha20 — authentifiés, pas de CBC)
STRONG_CIPHERS = {
    "chacha20-poly1305@openssh.com",
    "aes128-gcm@openssh.com",
    "aes256-gcm@openssh.com",
    "aes128-ctr", "aes192-ctr", "aes256-ctr",
}

# MACs faibles (MD5, SHA-1 non tronqué)
WEAK_MACS = {
    "hmac-md5", "hmac-md5-96", "hmac-sha1", "hmac-sha1-96",
    "hmac-ripemd160", "umac-64@openssh.com",
}

# MACs recommandés (ETM = Encrypt-then-MAC, SHA-2)
STRONG_MACS = {
    "hmac-sha2-256-etm@openssh.com", "hmac-sha2-512-etm@openssh.com",
    "umac-128-etm@openssh.com", "hmac-sha2-256", "hmac-sha2-512",
}

# Algorithmes d'échange de clés faibles
WEAK_KEX = {
    "diffie-hellman-group1-sha1",        # Logjam
    "diffie-hellman-group14-sha1",       # SHA-1 cassé
    "diffie-hellman-group-exchange-sha1",
    "gss-gex-sha1-*", "gss-group1-sha1-*",
}

# KEX recommandés (Curve25519, ECDH P-256/384, DH-GEX avec SHA-2)
STRONG_KEX = {
    "curve25519-sha256", "curve25519-sha256@libssh.org",
    "ecdh-sha2-nistp256", "ecdh-sha2-nistp384", "ecdh-sha2-nistp521",
    "diffie-hellman-group14-sha256",
    "diffie-hellman-group16-sha512",
    "diffie-hellman-group18-sha512",
}

SSH_CONFIG = "/etc/ssh/sshd_config"


def _get_directive(ssh, directive):
    """Lit une directive sshd_config (gère les commentaires et la casse)."""
    out, _ = ssh.execute_command(
        f"grep -i '^[[:space:]]*{directive}[[:space:]]' {SSH_CONFIG} 2>/dev/null | tail -1 | awk '{{print $2}}'"
    )
    return out.strip()


def _get_active_value(ssh, directive):
    """Retourne la valeur active via sshd -T (configuration compilée, plus fiable)."""
    out, _ = ssh.execute_command(f"sshd -T 2>/dev/null | grep -i '^{directive.lower()} ' | awk '{{print $2}}'")
    return out.strip()


def run_audit(ssh, rules):
    findings = []
    passed = []

    # Préférer sshd -T (valeurs actives) si disponible
    test_out, _ = ssh.execute_command("sshd -T 2>/dev/null | head -1")
    use_sshd_t = bool(test_out.strip())

    def get_val(directive, fallback_default=""):
        if use_sshd_t:
            v = _get_active_value(ssh, directive)
            if v:
                return v
        v = _get_directive(ssh, directive)
        return v or fallback_default

    # ──────────────────────────────────────────────────────────────────
    # 1. Checks de base (authentication & access)
    # ──────────────────────────────────────────────────────────────────

    basic_checks = [
        ("PermitRootLogin",       rules.get("root_login", "no"),        "HIGH",   "SSH-001",
         "Connexion SSH root directe autorisée"),
        ("PasswordAuthentication", rules.get("password_auth", "no"),    "HIGH",   "SSH-002",
         "Authentification par mot de passe SSH activée"),
        ("PermitEmptyPasswords",   rules.get("permit_empty_passwords","no"), "CRITICAL", "SSH-003",
         "Mots de passe vides autorisés"),
        ("X11Forwarding",          rules.get("x11_forwarding", "no"),   "MEDIUM", "SSH-004",
         "X11 Forwarding activé — risque de capture d'écran/clavier"),
        ("AllowAgentForwarding",   "no",                                 "MEDIUM", "SSH-005",
         "Agent forwarding activé — permet de rebondir sur d'autres serveurs"),
        ("AllowTcpForwarding",     "no",                                 "MEDIUM", "SSH-006",
         "TCP forwarding activé — tunneling non contrôlé"),
        ("UsePAM",                 "yes",                                "MEDIUM", "SSH-007",
         "PAM désactivé — perd les contrôles d'authentification système"),
        ("PrintLastLog",           "yes",                                "LOW",    "SSH-008",
         "Affichage de la dernière connexion désactivé"),
        ("Banner",                 "",                                   "LOW",    "SSH-009",
         "Bannière légale SSH absente"),
        ("LogLevel",               "VERBOSE",                            "LOW",    "SSH-010",
         "Niveau de log SSH insuffisant pour l'audit"),
        ("GSSAPIAuthentication",   "no",                                 "LOW",    "SSH-011",
         "GSSAPI activé sans Kerberos — surface d'attaque inutile"),
        ("IgnoreRhosts",           "yes",                                "HIGH",   "SSH-012",
         "rhosts ignorés — vecteur d'authentification faible"),
        ("HostbasedAuthentication","no",                                 "HIGH",   "SSH-013",
         "Authentification basée sur l'hôte activée"),
        ("Protocol",               "2",                                  "CRITICAL","SSH-014",
         "SSHv1 encore actif — protocole cassé depuis 2001"),
    ]

    for directive, expected, severity, check_id, description in basic_checks:
        found = get_val(directive)
        if directive == "Banner":
            # Banner doit juste être défini (non vide et non "none")
            if not found or found.lower() == "none":
                findings.append({
                    "check": check_id,
                    "check_name": directive,
                    "description": description,
                    "found": found or "non défini",
                    "expected": "/etc/issue.net ou équivalent",
                    "severity": severity,
                    "remediation": "echo 'Authorized access only' > /etc/issue.net && echo 'Banner /etc/issue.net' >> /etc/ssh/sshd_config",
                })
            else:
                passed.append({"check": check_id, "check_name": directive, "found": found})
            continue

        found_lower = found.lower() if found else ""
        expected_lower = expected.lower()

        if not found:
            # Non défini — utiliser la valeur par défaut OpenSSH et comparer
            default_map = {
                "ssh-009": "",
                "ssh-007": "yes",
                "ssh-008": "yes",
                "ssh-012": "yes",
                "ssh-014": "2",
            }
            found_lower = default_map.get(check_id.lower(), "")

        if found_lower and found_lower != expected_lower:
            findings.append({
                "check": check_id,
                "check_name": directive,
                "description": description,
                "found": found or "défaut OpenSSH",
                "expected": expected,
                "severity": severity,
                "remediation": f"echo '{directive} {expected}' >> {SSH_CONFIG} && systemctl restart sshd",
            })
        else:
            passed.append({"check": check_id, "check_name": directive, "found": found or f"défaut ({expected})"})

    # ──────────────────────────────────────────────────────────────────
    # 2. MaxAuthTries
    # ──────────────────────────────────────────────────────────────────
    max_tries_str = get_val("MaxAuthTries", "6")
    max_allowed = rules.get("max_auth_tries", 4)
    try:
        max_tries_val = int(max_tries_str)
        if max_tries_val > max_allowed:
            findings.append({
                "check": "SSH-015",
                "check_name": "MaxAuthTries",
                "description": f"Trop de tentatives d'authentification autorisées ({max_tries_val} > {max_allowed})",
                "found": str(max_tries_val),
                "expected": f"<= {max_allowed}",
                "severity": "MEDIUM",
                "remediation": f"sed -i 's/^#*MaxAuthTries.*/MaxAuthTries {max_allowed}/' {SSH_CONFIG} && systemctl restart sshd",
            })
        else:
            passed.append({"check": "SSH-015", "check_name": "MaxAuthTries", "found": str(max_tries_val)})
    except ValueError:
        passed.append({"check": "SSH-015", "check_name": "MaxAuthTries", "found": f"défaut (6)"})

    # ──────────────────────────────────────────────────────────────────
    # 3. ClientAliveInterval / ClientAliveCountMax (session timeout)
    # ──────────────────────────────────────────────────────────────────
    interval = get_val("ClientAliveInterval", "0")
    try:
        if int(interval) == 0:
            findings.append({
                "check": "SSH-016",
                "check_name": "ClientAliveInterval",
                "description": "Pas de timeout de session SSH — sessions inactives non terminées",
                "found": "0 (désactivé)",
                "expected": "<= 300 (5 minutes)",
                "severity": "MEDIUM",
                "remediation": f"echo 'ClientAliveInterval 300\nClientAliveCountMax 3' >> {SSH_CONFIG} && systemctl restart sshd",
            })
        else:
            passed.append({"check": "SSH-016", "check_name": "ClientAliveInterval", "found": f"{interval}s"})
    except ValueError:
        pass

    # ──────────────────────────────────────────────────────────────────
    # 4. Ciphers — détection des algorithmes faibles
    # ──────────────────────────────────────────────────────────────────
    ciphers_raw = get_val("Ciphers")
    if ciphers_raw:
        active_ciphers = {c.strip() for c in ciphers_raw.split(",")}
        weak_found = active_ciphers & WEAK_CIPHERS
        if weak_found:
            findings.append({
                "check": "SSH-020",
                "check_name": "Ciphers (algorithmes faibles)",
                "description": f"Ciphers CBC ou faibles détectés — vulnérables aux attaques padding oracle",
                "found": ", ".join(sorted(weak_found)),
                "expected": "Uniquement AES-GCM / ChaCha20-Poly1305 / AES-CTR",
                "severity": "HIGH",
                "remediation": "echo 'Ciphers chacha20-poly1305@openssh.com,aes256-gcm@openssh.com,aes128-gcm@openssh.com,aes256-ctr,aes192-ctr,aes128-ctr' >> "
                               + SSH_CONFIG + " && systemctl restart sshd",
            })
        else:
            passed.append({
                "check": "SSH-020",
                "check_name": "Ciphers",
                "found": f"Aucun cipher faible ({len(active_ciphers)} ciphers actifs)",
            })
    else:
        # Ciphers non explicitement définis = valeur défaut OpenSSH (généralement ok en v8+)
        passed.append({"check": "SSH-020", "check_name": "Ciphers", "found": "Ciphers par défaut OpenSSH (vérifier version)"})

    # ──────────────────────────────────────────────────────────────────
    # 5. MACs — détection des algorithmes d'intégrité faibles
    # ──────────────────────────────────────────────────────────────────
    macs_raw = get_val("MACs")
    if macs_raw:
        active_macs = {m.strip() for m in macs_raw.split(",")}
        weak_found = active_macs & WEAK_MACS
        if weak_found:
            findings.append({
                "check": "SSH-021",
                "check_name": "MACs (algorithmes d'intégrité faibles)",
                "description": "MACs MD5 ou SHA-1 détectés — vulnérables aux collisions",
                "found": ", ".join(sorted(weak_found)),
                "expected": "Uniquement HMAC-SHA2-256-ETM / HMAC-SHA2-512-ETM",
                "severity": "HIGH",
                "remediation": "echo 'MACs hmac-sha2-256-etm@openssh.com,hmac-sha2-512-etm@openssh.com,umac-128-etm@openssh.com' >> "
                               + SSH_CONFIG + " && systemctl restart sshd",
            })
        else:
            passed.append({
                "check": "SSH-021",
                "check_name": "MACs",
                "found": f"Aucun MAC faible ({len(active_macs)} MACs actifs)",
            })
    else:
        passed.append({"check": "SSH-021", "check_name": "MACs", "found": "MACs par défaut OpenSSH"})

    # ──────────────────────────────────────────────────────────────────
    # 6. KexAlgorithms — échange de clés
    # ──────────────────────────────────────────────────────────────────
    kex_raw = get_val("KexAlgorithms")
    if kex_raw:
        active_kex = {k.strip() for k in kex_raw.split(",")}
        weak_found = {k for k in active_kex if any(k.startswith(w.rstrip("*")) for w in WEAK_KEX)}
        if weak_found:
            findings.append({
                "check": "SSH-022",
                "check_name": "KexAlgorithms (échange de clés faibles)",
                "description": "Algorithmes DH avec SHA-1 ou groupe 1 (Logjam) détectés",
                "found": ", ".join(sorted(weak_found)),
                "expected": "Curve25519, ECDH P-256/384, DH-GEX SHA-256+",
                "severity": "HIGH",
                "remediation": "echo 'KexAlgorithms curve25519-sha256,curve25519-sha256@libssh.org,ecdh-sha2-nistp256,diffie-hellman-group16-sha512' >> "
                               + SSH_CONFIG + " && systemctl restart sshd",
            })
        else:
            passed.append({
                "check": "SSH-022",
                "check_name": "KexAlgorithms",
                "found": f"Aucun KEX faible ({len(active_kex)} algorithmes actifs)",
            })
    else:
        passed.append({"check": "SSH-022", "check_name": "KexAlgorithms", "found": "KEX par défaut OpenSSH"})

    # ──────────────────────────────────────────────────────────────────
    # 7. Version OpenSSH — détecter les versions End-of-Life
    # ──────────────────────────────────────────────────────────────────
    out, _ = ssh.execute_command("ssh -V 2>&1 | head -1")
    if out.strip():
        try:
            # Format: OpenSSH_8.9p1 Ubuntu-3ubuntu0.6, OpenSSL 3.0.2
            version_str = out.split("_")[1].split("p")[0] if "_" in out else ""
            major, minor = int(version_str.split(".")[0]), int(version_str.split(".")[1])
            if (major, minor) < (7, 4):
                findings.append({
                    "check": "SSH-023",
                    "check_name": "OpenSSH version (EOL)",
                    "description": f"OpenSSH < 7.4 — version End-of-Life avec CVE critiques connues",
                    "found": out.strip(),
                    "expected": ">= 8.x recommandé",
                    "severity": "CRITICAL",
                    "remediation": "Mettre à jour OpenSSH via le gestionnaire de paquets",
                })
            else:
                passed.append({"check": "SSH-023", "check_name": "OpenSSH version", "found": out.strip()})
        except (IndexError, ValueError):
            passed.append({"check": "SSH-023", "check_name": "OpenSSH version", "found": out.strip()})

    return {
        "findings": findings,
        "passed": passed,
        "summary": {
            "total_checks": len(findings) + len(passed),
            "passed": len(passed),
            "failed": len(findings),
        }
    }
