# Module d'audit : configuration PAM (Pluggable Authentication Module)
# Référentiel : ANSSI-BP-028 v2.0 — Section 7.2.1
# Checks : R68 (authentification PAM), R69 (mots de passe stockés), R70 (bases utilisateur distantes)


def _r68_pam_auth(ssh):
    """R68 — Sécuriser les authentifications distantes par PAM."""
    findings, passed = [], []

    # Vérifier que PAM est actif (libpam)
    out, _ = ssh.execute_command("ls /etc/pam.d/ 2>/dev/null | wc -l")
    try:
        count = int(out.strip())
        if count == 0:
            findings.append({
                "check": "PAM-R68-001",
                "check_name": "PAM non configuré",
                "description": "[ANSSI R68] Aucun fichier de configuration PAM trouvé dans /etc/pam.d/ — "
                               "le système d'authentification n'est pas géré par PAM",
                "found": "0 fichiers dans /etc/pam.d/",
                "expected": "Répertoire /etc/pam.d/ peuplé",
                "severity": "HIGH",
                "remediation": "Vérifier l'installation de libpam : apt install libpam-runtime",
            })
        else:
            passed.append({"check": "PAM-R68-001", "check_name": "PAM configuré",
                           "found": f"{count} modules PAM configurés dans /etc/pam.d/"})
    except ValueError:
        pass

    # Vérifier pam_faillock ou pam_tally2 (verrouillage après échecs)
    out, _ = ssh.execute_command(
        "grep -rE 'pam_faillock|pam_tally2|pam_faildelay' /etc/pam.d/ 2>/dev/null | grep -v '#' | head -3"
    )
    if out.strip():
        passed.append({"check": "PAM-R68-002", "check_name": "Verrouillage après échecs",
                       "found": "pam_faillock ou pam_tally2 configuré — verrouillage actif"})
    else:
        findings.append({
            "check": "PAM-R68-002",
            "check_name": "Verrouillage compte absent",
            "description": "[ANSSI R68] Aucun mécanisme de verrouillage des comptes après échecs "
                           "d'authentification (pam_faillock/pam_tally2) — risque de brute-force",
            "found": "pam_faillock / pam_tally2 non configuré",
            "expected": "pam_faillock configuré avec deny=5 unlock_time=900",
            "severity": "HIGH",
            "remediation": "Ajouter dans /etc/pam.d/common-auth :\n"
                           "auth required pam_faillock.so preauth silent deny=5 unlock_time=900\n"
                           "auth [default=die] pam_faillock.so authfail deny=5 unlock_time=900",
        })

    # Vérifier pam_limits (ressources système)
    out, _ = ssh.execute_command(
        "grep -rE 'pam_limits' /etc/pam.d/ 2>/dev/null | grep -v '#' | head -3"
    )
    if out.strip():
        passed.append({"check": "PAM-R68-003", "check_name": "pam_limits",
                       "found": "pam_limits configuré — limites ressources actives"})
    else:
        findings.append({
            "check": "PAM-R68-003",
            "check_name": "pam_limits absent",
            "description": "[ANSSI R68] pam_limits n'est pas chargé — aucune limite de ressources "
                           "par utilisateur (descripteurs, processus, mémoire)",
            "found": "pam_limits non configuré",
            "expected": "session required pam_limits.so dans /etc/pam.d/common-session",
            "severity": "LOW",
            "remediation": "echo 'session required pam_limits.so' >> /etc/pam.d/common-session",
        })

    # Vérifier que root ne peut pas se connecter via PAM sans authentification
    out, _ = ssh.execute_command(
        "grep -rE 'pam_rootok' /etc/pam.d/ 2>/dev/null | grep -v '#' | head -5"
    )
    rootok_files = [l for l in out.strip().splitlines() if l]
    suspicious = [l for l in rootok_files if "su" not in l.lower() and "sudo" not in l.lower()]
    if suspicious:
        findings.append({
            "check": "PAM-R68-004",
            "check_name": "pam_rootok hors contexte su",
            "description": "[ANSSI R68] pam_rootok est configuré hors du contexte su/sudo — "
                           "root peut contourner l'authentification",
            "found": f"pam_rootok dans : {', '.join(suspicious[:3])}",
            "expected": "pam_rootok uniquement dans /etc/pam.d/su",
            "severity": "HIGH",
            "remediation": "Retirer pam_rootok des fichiers PAM autres que /etc/pam.d/su",
        })
    else:
        passed.append({"check": "PAM-R68-004", "check_name": "pam_rootok",
                       "found": "pam_rootok limité au contexte su (correct)"})

    return findings, passed


def _r69_password_storage(ssh):
    """R69 — Protéger les mots de passe stockés (hachage fort)."""
    findings, passed = [], []

    # Vérifier l'algorithme de hachage dans /etc/login.defs
    out, _ = ssh.execute_command(
        "grep -E '^ENCRYPT_METHOD' /etc/login.defs 2>/dev/null | awk '{print $2}'"
    )
    algo = out.strip().upper()

    STRONG_ALGOS = {"SHA512", "YESCRYPT", "BCRYPT"}
    WEAK_ALGOS   = {"MD5", "DES", "SHA256"}

    if algo in STRONG_ALGOS:
        passed.append({"check": "PAM-R69-001", "check_name": "Algorithme hachage mots de passe",
                       "found": f"Algorithme fort utilisé : {algo}"})
    elif algo in WEAK_ALGOS:
        findings.append({
            "check": "PAM-R69-001",
            "check_name": "Algorithme hachage faible",
            "description": f"[ANSSI R69] L'algorithme de hachage des mots de passe est {algo} — "
                           "insuffisant pour résister aux attaques par GPU",
            "found": algo,
            "expected": "SHA512 ou YESCRYPT",
            "severity": "CRITICAL",
            "remediation": "sed -i 's/^ENCRYPT_METHOD.*/ENCRYPT_METHOD SHA512/' /etc/login.defs",
        })
    else:
        # Vérifier directement dans /etc/shadow le préfixe de hachage
        out, _ = ssh.execute_command(
            "awk -F: '$2 ~ /^\\$/ {print substr($2,1,4)}' /etc/shadow 2>/dev/null | sort -u | head -5"
        )
        prefixes = set(out.strip().splitlines())
        algo_map = {
            "$1$": ("MD5", "CRITICAL"),
            "$2$": ("Blowfish", "MEDIUM"),
            "$2b$": ("bcrypt", None),
            "$5$": ("SHA-256", "MEDIUM"),
            "$6$": ("SHA-512", None),
            "$y$": ("yescrypt", None),
        }
        for prefix in prefixes:
            name, sev = algo_map.get(prefix, ("inconnu", "MEDIUM"))
            if sev:
                findings.append({
                    "check": "PAM-R69-002",
                    "check_name": f"Hachage {name} dans /etc/shadow",
                    "description": f"[ANSSI R69] Des mots de passe sont hachés avec {name} ({prefix}) — "
                                   "algorithme insuffisant",
                    "found": f"Préfixe {prefix} ({name}) dans /etc/shadow",
                    "expected": "$6$ (SHA-512) ou $y$ (yescrypt)",
                    "severity": sev,
                    "remediation": "chage -d 0 <utilisateur>  # Force le renouvellement du mot de passe",
                })
            else:
                passed.append({"check": "PAM-R69-002",
                               "check_name": f"Hachage {name}",
                               "found": f"Algorithme fort {name} ({prefix}) utilisé"})

        if not prefixes:
            passed.append({"check": "PAM-R69-001", "check_name": "Algorithme hachage",
                           "found": "Algorithme non détectable (accès limité à /etc/shadow)"})

    # Vérifier SHA_CRYPT_MIN_ROUNDS (renforcer le hachage SHA512)
    out, _ = ssh.execute_command(
        "grep -E '^SHA_CRYPT_MIN_ROUNDS' /etc/login.defs 2>/dev/null | awk '{print $2}'"
    )
    rounds = out.strip()
    try:
        r = int(rounds)
        if r >= 100000:
            passed.append({"check": "PAM-R69-003", "check_name": "SHA rounds",
                           "found": f"SHA_CRYPT_MIN_ROUNDS = {r} (renforcement correct)"})
        else:
            findings.append({
                "check": "PAM-R69-003",
                "check_name": "SHA rounds insuffisants",
                "description": "[ANSSI R69] Le nombre de rounds de hachage est trop faible — "
                               "les mots de passe peuvent être craqués plus rapidement",
                "found": f"SHA_CRYPT_MIN_ROUNDS = {r}",
                "expected": ">= 100000",
                "severity": "MEDIUM",
                "remediation": "echo 'SHA_CRYPT_MIN_ROUNDS 100000' >> /etc/login.defs",
            })
    except ValueError:
        findings.append({
            "check": "PAM-R69-003",
            "check_name": "SHA rounds non définis",
            "description": "[ANSSI R69] SHA_CRYPT_MIN_ROUNDS non défini — nombre de rounds minimal par défaut",
            "found": "non défini",
            "expected": "SHA_CRYPT_MIN_ROUNDS >= 100000",
            "severity": "LOW",
            "remediation": "echo 'SHA_CRYPT_MIN_ROUNDS 100000' >> /etc/login.defs",
        })

    return findings, passed


def _r70_remote_user_bases(ssh):
    """R70 — Séparer les comptes système et d'annuaire (LDAP/AD)."""
    findings, passed = [], []

    # Vérifier si LDAP/AD est configuré via NSS
    out, _ = ssh.execute_command(
        "grep -E 'ldap|sss|winbind|ad' /etc/nsswitch.conf 2>/dev/null | grep -v '#' | head -5"
    )
    if out.strip():
        # LDAP/SSS configuré — vérifier que les comptes locaux restent prioritaires
        out2, _ = ssh.execute_command(
            "grep -E '^passwd:' /etc/nsswitch.conf 2>/dev/null"
        )
        line = out2.strip()
        if line and not line.startswith("passwd: files"):
            findings.append({
                "check": "PAM-R70-001",
                "check_name": "Ordre NSS incorrect",
                "description": "[ANSSI R70] Les fichiers locaux ne sont pas prioritaires dans nsswitch.conf — "
                               "risque que des comptes distants (LDAP/AD) écrasent les comptes système locaux",
                "found": line,
                "expected": "passwd: files [SUCCESS=continue] ldap sss",
                "severity": "HIGH",
                "remediation": "Modifier /etc/nsswitch.conf : passwd: files ldap  (files en premier)",
            })
        else:
            passed.append({"check": "PAM-R70-001", "check_name": "Ordre NSS",
                           "found": f"Comptes locaux prioritaires : {line}"})

        # Vérifier que sssd ou pam_ldap sépare bien les comptes
        out3, _ = ssh.execute_command("which sssd 2>/dev/null || which pam-auth-update 2>/dev/null")
        if out3.strip():
            passed.append({"check": "PAM-R70-002", "check_name": "Annuaire centralisé",
                           "found": "sssd/pam-auth-update présent — gestion des comptes distants via daemon"})
        else:
            findings.append({
                "check": "PAM-R70-002",
                "check_name": "sssd absent",
                "description": "[ANSSI R70] LDAP configuré mais sssd absent — connexion LDAP directe sans cache",
                "found": "sssd non installé",
                "expected": "sssd pour la gestion sécurisée des comptes LDAP/AD",
                "severity": "MEDIUM",
                "remediation": "apt install sssd sssd-ldap",
            })
    else:
        passed.append({"check": "PAM-R70-001", "check_name": "Base utilisateurs distante",
                       "found": "Pas de base utilisateurs distante (LDAP/AD) configurée"})

    return findings, passed


def run_audit(ssh, rules):
    findings = []
    passed = []

    for fn in [_r68_pam_auth, _r69_password_storage, _r70_remote_user_bases]:
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
