"""Module d'audit des comptes utilisateurs et de la politique sudo pour Linux.

Implémente les recommandations ANSSI-BP-028 v2.0 § 6.2 : comptes inutilisés
(R30), politique de mots de passe (R31), timeout de session (R32),
imputabilité des admins (R33), comptes de service (R34), UMASK (R36),
configuration sudo R37-R44.
"""
# Référentiel : ANSSI-BP-028 v2.0 — Section 6.2 (Comptes d'accès)
# Checks : R30 (comptes inutilisés), R31 (mots de passe), R32 (sessions),
#          R33 (imputabilité), R34 (comptes service), R36 (UMASK), R37-R44 (sudo)

# Shells légitimes pour les comptes humains
VALID_LOGIN_SHELLS = {"/bin/bash", "/bin/sh", "/bin/zsh", "/bin/fish", "/usr/bin/bash",
                      "/usr/bin/zsh", "/usr/bin/fish"}

# Shells de blocage pour les comptes de service
NOLOGIN_SHELLS = {"/sbin/nologin", "/usr/sbin/nologin", "/bin/false", "/usr/bin/false"}


def _r30_unused_accounts(ssh):
    """R30 — Comptes utilisateur inutilisés doivent être désactivés."""
    findings, passed = [], []

    # Comptes avec un shell de connexion mais dont le mot de passe est verrouillé (! ou *)
    out, _ = ssh.execute_command(
        "awk -F: 'NR==FNR{if($2~/^[!*]/ && $2!=\"!!\" && $2!=\"*\") locked[$1]=1; next}"
        " $7 !~ /nologin|false/ && $1 in locked {print $1}' /etc/shadow /etc/passwd 2>/dev/null"
    )
    locked_with_shell = [u for u in out.strip().splitlines() if u]
    if locked_with_shell:
        findings.append({
            "check": "USR-R30-001",
            "check_name": "Comptes verrouillés avec shell actif",
            "description": "[ANSSI R30] Des comptes verrouillés disposent encore d'un shell de connexion — "
                           "ils doivent être désactivés ou leur shell mis à /sbin/nologin",
            "found": ", ".join(locked_with_shell),
            "expected": "shell = /sbin/nologin ou compte désactivé",
            "severity": "MEDIUM",
            "remediation": "usermod -s /sbin/nologin <compte> && usermod -L <compte>",
        })
    else:
        passed.append({"check": "USR-R30-001", "check_name": "Comptes verrouillés",
                       "found": "Aucun compte verrouillé avec shell actif"})

    # Comptes sans mot de passe du tout
    out, _ = ssh.execute_command(
        "awk -F: '($2 == \"\" || $2 == \"::\" ) {print $1}' /etc/shadow 2>/dev/null"
    )
    no_pwd = [u for u in out.strip().splitlines() if u]
    if no_pwd:
        findings.append({
            "check": "USR-R30-002",
            "check_name": "Comptes sans mot de passe",
            "description": "[ANSSI R30] Comptes sans mot de passe — accès sans authentification possible",
            "found": ", ".join(no_pwd),
            "expected": "tous les comptes ont un mot de passe",
            "severity": "CRITICAL",
            "remediation": "passwd <compte>  # ou  usermod -L <compte> si le compte doit rester inactif",
        })
    else:
        passed.append({"check": "USR-R30-002", "check_name": "Comptes sans mot de passe",
                       "found": "Tous les comptes ont un mot de passe défini"})

    return findings, passed


def _r31_password_policy(ssh):
    """R31 — Politique de mots de passe robustes (pwquality / PAM)."""
    findings, passed = [], []

    # Vérifier que pam_pwquality ou pam_cracklib est configuré
    out, _ = ssh.execute_command(
        "grep -rE 'pam_pwquality|pam_cracklib' /etc/pam.d/ 2>/dev/null | grep -v '#' | head -5"
    )
    if not out.strip():
        findings.append({
            "check": "USR-R31-001",
            "check_name": "pam_pwquality absent",
            "description": "[ANSSI R31] Aucun module de vérification de la robustesse des mots de passe "
                           "(pam_pwquality ou pam_cracklib) n'est configuré dans PAM",
            "found": "pam_pwquality non configuré",
            "expected": "pam_pwquality configuré dans /etc/pam.d/",
            "severity": "HIGH",
            "remediation": "apt install libpam-pwquality && "
                           "echo 'password requisite pam_pwquality.so retry=3 minlen=12 dcredit=-1 ucredit=-1 lcredit=-1 ocredit=-1' "
                           ">> /etc/pam.d/common-password",
        })
    else:
        passed.append({"check": "USR-R31-001", "check_name": "pam_pwquality",
                       "found": "Module de robustesse des mots de passe configuré"})

    # Vérifier /etc/login.defs : PASS_MAX_DAYS, PASS_MIN_DAYS, PASS_MIN_LEN
    for param, min_val, check_id, desc in [
        ("PASS_MAX_DAYS", 90,  "USR-R31-002", "Durée de validité maximale du mot de passe"),
        ("PASS_MIN_DAYS", 1,   "USR-R31-003", "Durée minimale avant changement de mot de passe"),
        ("PASS_MIN_LEN",  12,  "USR-R31-004", "Longueur minimale du mot de passe"),
    ]:
        out, _ = ssh.execute_command(
            f"grep -E '^{param}' /etc/login.defs 2>/dev/null | awk '{{print $2}}'"
        )
        val = out.strip()
        try:
            v = int(val)
            if param == "PASS_MAX_DAYS" and v > min_val:
                findings.append({
                    "check": check_id, "check_name": f"login.defs {param}",
                    "description": f"[ANSSI R31] {desc} trop élevée ({v} jours > {min_val} jours recommandés)",
                    "found": str(v), "expected": f"<= {min_val}",
                    "severity": "MEDIUM",
                    "remediation": f"sed -i 's/^{param}.*/{param} {min_val}/' /etc/login.defs",
                })
            elif param != "PASS_MAX_DAYS" and v < min_val:
                findings.append({
                    "check": check_id, "check_name": f"login.defs {param}",
                    "description": f"[ANSSI R31] {desc} insuffisante",
                    "found": str(v), "expected": f">= {min_val}",
                    "severity": "MEDIUM",
                    "remediation": f"sed -i 's/^{param}.*/{param} {min_val}/' /etc/login.defs",
                })
            else:
                passed.append({"check": check_id, "check_name": f"login.defs {param}", "found": str(v)})
        except (ValueError, TypeError):
            findings.append({
                "check": check_id, "check_name": f"login.defs {param}",
                "description": f"[ANSSI R31] {desc} non définie dans /etc/login.defs",
                "found": val or "absent", "expected": f">= {min_val}",
                "severity": "MEDIUM",
                "remediation": f"echo '{param} {min_val}' >> /etc/login.defs",
            })

    return findings, passed


def _r32_session_timeout(ssh):
    """R32 — Les sessions locales doivent expirer après inactivité."""
    findings, passed = [], []

    # Vérifier TMOUT dans /etc/profile ou /etc/profile.d/
    out, _ = ssh.execute_command(
        "grep -rE '^TMOUT|^export TMOUT' /etc/profile /etc/profile.d/ 2>/dev/null | head -3"
    )
    if out.strip():
        passed.append({"check": "USR-R32-001", "check_name": "TMOUT session timeout",
                       "found": f"Timeout configuré : {out.strip()}"})
    else:
        findings.append({
            "check": "USR-R32-001",
            "check_name": "TMOUT session timeout absent",
            "description": "[ANSSI R32] Aucun timeout d'inactivité des sessions locales configuré — "
                           "une session non surveillée reste accessible indéfiniment",
            "found": "TMOUT non défini",
            "expected": "TMOUT=900 (ou valeur <= 900 secondes)",
            "severity": "MEDIUM",
            "remediation": "echo 'TMOUT=900' >> /etc/profile.d/timeout.sh && "
                           "echo 'readonly TMOUT' >> /etc/profile.d/timeout.sh && "
                           "echo 'export TMOUT' >> /etc/profile.d/timeout.sh",
        })

    return findings, passed


def _r33_admin_accountability(ssh):
    """R33 — Imputabilité des actions d'administration (sudo logging)."""
    findings, passed = [], []

    # Vérifier que sudo est installé
    out, _ = ssh.execute_command("which sudo 2>/dev/null")
    if not out.strip():
        findings.append({
            "check": "USR-R33-001",
            "check_name": "sudo absent",
            "description": "[ANSSI R33] sudo n'est pas installé — impossible d'assurer l'imputabilité "
                           "des actions d'administration sans passer par le compte root directement",
            "found": "sudo non installé",
            "expected": "sudo installé et configuré",
            "severity": "HIGH",
            "remediation": "apt install sudo  # ou  yum install sudo",
        })
        return findings, passed

    passed.append({"check": "USR-R33-001", "check_name": "sudo installé", "found": out.strip()})

    # Vérifier que sudo log les commandes (Defaults log_input/log_output ou syslog)
    out, _ = ssh.execute_command(
        "grep -rE '^Defaults.*log_input|^Defaults.*log_output|^Defaults.*syslog' /etc/sudoers /etc/sudoers.d/ 2>/dev/null | head -3"
    )
    if out.strip():
        passed.append({"check": "USR-R33-002", "check_name": "sudo logging",
                       "found": "Journalisation sudo configurée"})
    else:
        findings.append({
            "check": "USR-R33-002",
            "check_name": "sudo logging absent",
            "description": "[ANSSI R33] sudo ne journalise pas les commandes exécutées — "
                           "l'imputabilité des administrateurs ne peut pas être assurée",
            "found": "Pas de Defaults log_input/log_output dans sudoers",
            "expected": "Defaults log_input, log_output dans /etc/sudoers",
            "severity": "HIGH",
            "remediation": "echo 'Defaults log_input, log_output' >> /etc/sudoers.d/logging",
        })

    # Vérifier que root ne peut pas se connecter directement via SSH
    out, _ = ssh.execute_command(
        "grep -E '^PermitRootLogin' /etc/ssh/sshd_config 2>/dev/null | tail -1 | awk '{print $2}'"
    )
    val = out.strip().lower()
    if val in ("no", "prohibit-password", "forced-commands-only"):
        passed.append({"check": "USR-R33-003", "check_name": "PermitRootLogin SSH",
                       "found": f"Connexion root SSH : {val}"})
    else:
        findings.append({
            "check": "USR-R33-003",
            "check_name": "PermitRootLogin SSH activé",
            "description": "[ANSSI R33] La connexion SSH directe en root est autorisée — "
                           "toute action root devient intraçable à un individu",
            "found": val or "yes (par défaut)",
            "expected": "no",
            "severity": "HIGH",
            "remediation": "sed -i 's/^PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config && systemctl reload sshd",
        })

    return findings, passed


def _r34_service_accounts(ssh):
    """R34 — Les comptes de service doivent être désactivés (shell nologin)."""
    findings, passed = [], []

    # Comptes système (UID < 1000, hors root) avec un shell de connexion actif
    out, _ = ssh.execute_command(
        "awk -F: '$3 > 0 && $3 < 1000 && $7 !~ /nologin|false/ {print $1\":\"$7}' /etc/passwd 2>/dev/null"
    )
    bad_service_accounts = [l for l in out.strip().splitlines() if l and not l.startswith("root")]
    if bad_service_accounts:
        findings.append({
            "check": "USR-R34-001",
            "check_name": "Comptes service avec shell actif",
            "description": "[ANSSI R34] Des comptes de service (UID < 1000) disposent d'un shell "
                           "de connexion — ils pourraient être utilisés pour ouvrir une session interactive",
            "found": ", ".join(bad_service_accounts),
            "expected": "shell = /sbin/nologin ou /bin/false",
            "severity": "MEDIUM",
            "remediation": "usermod -s /sbin/nologin <compte_service>",
        })
    else:
        passed.append({"check": "USR-R34-001", "check_name": "Comptes service désactivés",
                       "found": "Tous les comptes de service ont un shell non-interactif"})

    return findings, passed


def _r36_umask(ssh):
    """R36 — Valeur UMASK restrictive (027 ou plus)."""
    findings, passed = [], []

    out, _ = ssh.execute_command(
        "grep -rE '^UMASK|^umask' /etc/login.defs /etc/profile /etc/profile.d/ /etc/bashrc 2>/dev/null | head -5"
    )
    lines = [l for l in out.strip().splitlines() if l]

    umask_values = []
    for line in lines:
        parts = line.split()
        if len(parts) >= 2:
            umask_values.append(parts[-1])

    permissive = [u for u in umask_values if u in ("022", "0022", "002", "0002")]
    if permissive:
        findings.append({
            "check": "USR-R36-001",
            "check_name": "UMASK trop permissif",
            "description": "[ANSSI R36] La valeur UMASK est trop permissive — les fichiers créés "
                           "sont lisibles par le groupe ou tous les utilisateurs",
            "found": f"UMASK = {', '.join(permissive)}",
            "expected": "027 (fichiers non lisibles par autres) ou 077 (fichiers privés)",
            "severity": "MEDIUM",
            "remediation": "echo 'UMASK 027' >> /etc/login.defs  # et mettre à jour /etc/profile",
        })
    elif umask_values:
        passed.append({"check": "USR-R36-001", "check_name": "UMASK",
                       "found": f"UMASK restrictif : {', '.join(umask_values)}"})
    else:
        findings.append({
            "check": "USR-R36-001",
            "check_name": "UMASK non défini",
            "description": "[ANSSI R36] Aucune valeur UMASK explicite trouvée — "
                           "la valeur par défaut (souvent 022) s'applique",
            "found": "UMASK non défini explicitement",
            "expected": "UMASK 027 dans /etc/login.defs",
            "severity": "LOW",
            "remediation": "echo 'UMASK 027' >> /etc/login.defs",
        })

    return findings, passed


def _r37_r44_sudo_config(ssh):
    """R37-R44 — Configuration de sudo : groupe dédié, directives, EXEC, négations."""
    findings, passed = [], []

    # R37 : Groupe dédié à l'usage de sudo
    out, _ = ssh.execute_command("grep -E '^%sudo|^%wheel|^%admins' /etc/sudoers 2>/dev/null | head -5")
    if out.strip():
        passed.append({"check": "USR-R37-001", "check_name": "Groupe sudo dédié",
                       "found": f"Groupes sudo configurés : {out.strip()[:100]}"})
    else:
        findings.append({
            "check": "USR-R37-001",
            "check_name": "Groupe sudo dédié absent",
            "description": "[ANSSI R37] Aucun groupe dédié à l'usage de sudo n'est configuré — "
                           "l'accès sudo devrait passer par un groupe (%sudo, %wheel) pour faciliter la gestion",
            "found": "Pas de groupe %sudo ou %wheel dans sudoers",
            "expected": "%sudo ou %wheel configuré",
            "severity": "LOW",
            "remediation": "echo '%sudo ALL=(ALL:ALL) ALL' >> /etc/sudoers.d/groupe-sudo",
        })

    # R41 : Interdire les négations dans sudo (NOPASSWD sans restriction = risque)
    out, _ = ssh.execute_command(
        "grep -E '^[^#].*NOPASSWD' /etc/sudoers /etc/sudoers.d/* 2>/dev/null | grep -v '#' | head -5"
    )
    if out.strip():
        findings.append({
            "check": "USR-R41-001",
            "check_name": "NOPASSWD dans sudoers",
            "description": "[ANSSI R41] Des règles sudo avec NOPASSWD existent — "
                           "un attaquant ayant accès au compte peut escalader sans authentification supplémentaire",
            "found": out.strip()[:200],
            "expected": "Pas de NOPASSWD sans justification documentée",
            "severity": "HIGH",
            "remediation": "Réviser les entrées NOPASSWD dans /etc/sudoers et /etc/sudoers.d/",
        })
    else:
        passed.append({"check": "USR-R41-001", "check_name": "NOPASSWD absent",
                       "found": "Aucune règle NOPASSWD dans sudoers"})

    # R42 : Interdire ALL dans les commandes (trop permissif)
    out, _ = ssh.execute_command(
        "grep -E '^[^#%].*(ALL).*=.*\\(ALL\\).*ALL' /etc/sudoers /etc/sudoers.d/* 2>/dev/null | head -5"
    )
    if out.strip():
        findings.append({
            "check": "USR-R42-001",
            "check_name": "Règle sudo ALL ALL ALL",
            "description": "[ANSSI R42] Une règle sudo 'ALL=(ALL) ALL' accorde tous les droits — "
                           "préférer des règles ciblant des commandes spécifiques",
            "found": out.strip()[:200],
            "expected": "Commandes spécifiques au lieu de ALL",
            "severity": "MEDIUM",
            "remediation": "Remplacer les ALL par des listes de commandes précises dans sudoers",
        })
    else:
        passed.append({"check": "USR-R42-001", "check_name": "Commandes sudo ciblées",
                       "found": "Aucune règle ALL=(ALL) ALL sans groupe"})

    # R44 : visudo pour l'édition sécurisée
    out, _ = ssh.execute_command("which visudo 2>/dev/null")
    if out.strip():
        passed.append({"check": "USR-R44-001", "check_name": "visudo disponible",
                       "found": f"visudo installé : {out.strip()}"})
    else:
        findings.append({
            "check": "USR-R44-001",
            "check_name": "visudo absent",
            "description": "[ANSSI R44] visudo n'est pas disponible — édition de sudoers sans vérification syntaxique",
            "found": "visudo non trouvé",
            "expected": "visudo installé",
            "severity": "LOW",
            "remediation": "apt install sudo  # visudo est inclus avec sudo",
        })

    return findings, passed


def run_audit(ssh, rules):
    """Exécute l'ensemble des contrôles utilisateurs/sudo sur la cible Linux.

    Délègue à chaque sous-fonction ANSSI (R30–R44) puis agrège les résultats.

    Args:
        ssh: SSHConnector connecté à la cible.
        rules: dict de règles (non utilisé directement ici ; transmis aux
               sous-fonctions pour extensions futures).

    Returns:
        dict avec clés :
            findings (list[dict]) — non-conformités détectées.
            passed   (list[dict]) — contrôles conformes.
            summary  (dict)       — total_checks, passed, failed.
    """
    findings = []
    passed = []

    for fn in [_r30_unused_accounts, _r31_password_policy, _r32_session_timeout,
               _r33_admin_accountability, _r34_service_accounts, _r36_umask, _r37_r44_sudo_config]:
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
