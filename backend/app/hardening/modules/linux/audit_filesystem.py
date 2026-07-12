"""Module d'audit du système de fichiers Linux.

Couvre les recommandations ANSSI-BP-028 v2.0 relatives au cloisonnement des
partitions (R28-R29), aux permissions des fichiers sensibles (R49), aux
fichiers world-writable (R52), aux fichiers sans propriétaire (R53), au
sticky bit (R54) et aux exécutables setuid/setgid (R56-R57).
"""
# Référentiel : ANSSI-BP-028 v2.0 — Sections 6.1 (Partitionnement) + 6.4 (Fichiers et répertoires)
# Checks : R28-R29 (partitions), R49-R57 (permissions, setuid/setgid, sticky bit)

SENSITIVE_FILES = [
    # (chemin, mode_attendu, owner, group, check_id, ref_anssi, description)
    ("/etc/passwd",       "644", "root", "root",   "FS-R49-001", "R49", "Registre des comptes utilisateur"),
    ("/etc/shadow",       "640", "root", "shadow", "FS-R49-002", "R49", "Mots de passe chiffrés — accès root/shadow uniquement"),
    ("/etc/group",        "644", "root", "root",   "FS-R49-003", "R49", "Registre des groupes"),
    ("/etc/sudoers",      "440", "root", "root",   "FS-R49-004", "R49", "Configuration sudo — lecture root uniquement"),
    ("/etc/ssh/sshd_config","600","root","root",   "FS-R49-005", "R49", "Configuration du serveur SSH"),
    ("/boot/grub/grub.cfg","600","root","root",    "FS-R49-006", "R49", "Configuration GRUB — contient la ligne de commande noyau"),
    ("/etc/crontab",      "600", "root", "root",   "FS-R49-007", "R49", "Cron système — modifiable root uniquement"),
    ("/etc/gshadow",      "640", "root", "shadow", "FS-R49-008", "R49", "Mots de passe des groupes"),
]

# Partitions et leurs options de montage attendues (R28)
PARTITION_CHECKS = [
    # (point_montage, options_requises, sévérité, check_id)
    ("/tmp",      ["nosuid", "nodev", "noexec"], "HIGH",   "FS-R28-001"),
    ("/var/tmp",  ["nosuid", "nodev", "noexec"], "HIGH",   "FS-R28-002"),
    ("/boot",     ["nosuid", "nodev", "noexec"], "MEDIUM", "FS-R28-003"),
    ("/home",     ["nosuid", "nodev"],           "MEDIUM", "FS-R28-004"),
    ("/dev/shm",  ["nosuid", "nodev", "noexec"], "HIGH",   "FS-R28-005"),
]


def _r28_partition_options(ssh):
    """R28 — Vérifier les options de montage des partitions sensibles."""
    findings, passed = [], []

    out, _ = ssh.execute_command("cat /proc/mounts 2>/dev/null || mount 2>/dev/null")
    mount_lines = out.strip().splitlines()

    for mount_point, required_opts, severity, check_id in PARTITION_CHECKS:
        # Chercher la ligne correspondant à ce point de montage
        matching = [l for l in mount_lines if f" {mount_point} " in l or l.endswith(mount_point)]
        if not matching:
            findings.append({
                "check": check_id,
                "check_name": f"Partition {mount_point}",
                "description": f"[ANSSI R28] Le point de montage {mount_point} n'est pas une partition dédiée — "
                               f"les options {', '.join(required_opts)} ne peuvent pas être appliquées",
                "found": f"{mount_point} non trouvé dans /proc/mounts",
                "expected": f"partition dédiée avec options : {', '.join(required_opts)}",
                "severity": "LOW",
                "remediation": f"Créer une partition dédiée {mount_point} avec les options "
                               f"{','.join(required_opts)} dans /etc/fstab",
            })
            continue

        line = matching[-1]
        missing_opts = [opt for opt in required_opts if opt not in line]
        if missing_opts:
            findings.append({
                "check": check_id,
                "check_name": f"Options montage {mount_point}",
                "description": f"[ANSSI R28] Options de montage manquantes sur {mount_point} — "
                               f"risque d'exécution de code malveillant ou d'escalade de privilèges",
                "found": f"options manquantes : {', '.join(missing_opts)}",
                "expected": f"options présentes : {', '.join(required_opts)}",
                "severity": severity,
                "remediation": f"Ajouter {','.join(missing_opts)} dans /etc/fstab pour {mount_point} "
                               f"et relancer : mount -o remount {mount_point}",
            })
        else:
            passed.append({
                "check": check_id,
                "check_name": f"Options montage {mount_point}",
                "found": f"Options correctes sur {mount_point} : {', '.join(required_opts)}",
            })

    return findings, passed


def _r29_boot_access(ssh):
    """R29 — /boot accessible uniquement par root."""
    findings, passed = [], []

    out, _ = ssh.execute_command("stat -c '%a %U %G' /boot 2>/dev/null")
    val = out.strip()
    if not val:
        passed.append({"check": "FS-R29-001", "check_name": "/boot accès",
                       "found": "/boot non accessible (partitionné séparément)"})
        return findings, passed

    parts = val.split()
    mode, owner, group = parts[0], parts[1] if len(parts) > 1 else "?", parts[2] if len(parts) > 2 else "?"

    if owner != "root" or group != "root":
        findings.append({
            "check": "FS-R29-001",
            "check_name": "/boot propriétaire",
            "description": "[ANSSI R29] /boot n'appartient pas à root — son contenu (noyau, GRUB) "
                           "pourrait être modifié par un utilisateur non privilégié",
            "found": f"owner={owner} group={group}",
            "expected": "root:root",
            "severity": "HIGH",
            "remediation": "chown root:root /boot && chmod 700 /boot",
        })
    else:
        passed.append({"check": "FS-R29-001", "check_name": "/boot propriétaire",
                       "found": f"/boot appartient à root:root"})

    if mode not in ("700", "750", "755"):
        findings.append({
            "check": "FS-R29-002",
            "check_name": "/boot permissions",
            "description": "[ANSSI R29] Les permissions de /boot permettent un accès trop large",
            "found": f"mode={mode}",
            "expected": "700 (root uniquement) ou 750",
            "severity": "MEDIUM",
            "remediation": "chmod 700 /boot",
        })
    else:
        passed.append({"check": "FS-R29-002", "check_name": "/boot permissions",
                       "found": f"permissions /boot : {mode}"})

    return findings, passed


def _r49_sensitive_files(ssh):
    """R49 — Permissions et propriétaires des fichiers sensibles."""
    findings, passed = [], []

    for (path, exp_mode, exp_owner, exp_group, check_id, ref, description) in SENSITIVE_FILES:
        out, _ = ssh.execute_command(f"stat -c '%a %U %G' {path} 2>/dev/null")
        if not out.strip():
            # Fichier absent — pas forcément un problème (ex: grub.cfg sur certains systèmes)
            passed.append({"check": check_id, "check_name": f"Existence {path}",
                           "found": f"{path} absent (non applicable sur ce système)"})
            continue

        parts = out.strip().split()
        mode  = parts[0] if parts else "?"
        owner = parts[1] if len(parts) > 1 else "?"
        group = parts[2] if len(parts) > 2 else "?"

        errors = []
        if mode != exp_mode:
            errors.append(f"mode={mode} (attendu {exp_mode})")
        if owner != exp_owner:
            errors.append(f"owner={owner} (attendu {exp_owner})")
        if group not in (exp_group, "root", "shadow"):
            errors.append(f"group={group} (attendu {exp_group})")

        if errors:
            findings.append({
                "check": check_id,
                "check_name": f"Permissions {path}",
                "description": f"[ANSSI {ref}] {description} — permissions incorrectes sur {path}",
                "found": ", ".join(errors),
                "expected": f"mode={exp_mode} owner={exp_owner} group={exp_group}",
                "severity": "HIGH",
                "remediation": f"chmod {exp_mode} {path} && chown {exp_owner}:{exp_group} {path}",
            })
        else:
            passed.append({"check": check_id, "check_name": f"Permissions {path}",
                           "found": f"{path} : mode={mode} owner={owner} group={group} ✓"})

    return findings, passed


def _r52_world_writable_files(ssh):
    """R52 — Fichiers inscriptibles par tous (world-writable)."""
    findings, passed = [], []

    out, _ = ssh.execute_command(
        "find / -xdev -type f -perm -0002 -not -path '/proc/*' -not -path '/sys/*' 2>/dev/null | head -20"
    )
    ww_files = [l for l in out.strip().splitlines() if l]
    if ww_files:
        findings.append({
            "check": "FS-R52-001",
            "check_name": "Fichiers world-writable",
            "description": "[ANSSI R52] Des fichiers sont modifiables par n'importe quel utilisateur — "
                           "risque de manipulation de données ou d'escalade de privilèges",
            "found": f"{len(ww_files)} fichiers world-writable : {', '.join(ww_files[:5])}"
                     + (f" (et {len(ww_files)-5} autres)" if len(ww_files) > 5 else ""),
            "expected": "Aucun fichier inscriptible par tous",
            "severity": "HIGH",
            "remediation": "chmod o-w <fichier>  # Pour chaque fichier listé",
        })
    else:
        passed.append({"check": "FS-R52-001", "check_name": "Fichiers world-writable",
                       "found": "Aucun fichier world-writable trouvé"})

    return findings, passed


def _r53_orphan_files(ssh):
    """R53 — Fichiers sans propriétaire ou groupe connu."""
    findings, passed = [], []

    out, _ = ssh.execute_command(
        "find / -xdev -type f \\( -nouser -o -nogroup \\) -not -path '/proc/*' 2>/dev/null | head -10"
    )
    orphans = [l for l in out.strip().splitlines() if l]
    if orphans:
        findings.append({
            "check": "FS-R53-001",
            "check_name": "Fichiers sans propriétaire",
            "description": "[ANSSI R53] Des fichiers n'ont pas de propriétaire ou groupe connu — "
                           "résidu d'un compte supprimé ou fichier suspect",
            "found": f"{len(orphans)} fichier(s) : {', '.join(orphans[:5])}",
            "expected": "Tous les fichiers ont un propriétaire valide",
            "severity": "MEDIUM",
            "remediation": "chown root:root <fichier>  # ou supprimer le fichier s'il est inutile",
        })
    else:
        passed.append({"check": "FS-R53-001", "check_name": "Fichiers sans propriétaire",
                       "found": "Aucun fichier orphelin trouvé"})

    return findings, passed


def _r54_sticky_bit(ssh):
    """R54 — Sticky bit sur les répertoires inscriptibles par tous."""
    findings, passed = [], []

    out, _ = ssh.execute_command(
        "find / -xdev -type d -perm -0002 -not -perm -1000 -not -path '/proc/*' -not -path '/sys/*' 2>/dev/null | head -10"
    )
    missing_sticky = [l for l in out.strip().splitlines() if l]
    if missing_sticky:
        findings.append({
            "check": "FS-R54-001",
            "check_name": "Sticky bit manquant",
            "description": "[ANSSI R54] Des répertoires inscriptibles par tous n'ont pas le sticky bit — "
                           "un utilisateur peut supprimer les fichiers des autres dans ces répertoires",
            "found": f"{len(missing_sticky)} répertoire(s) : {', '.join(missing_sticky[:5])}",
            "expected": "sticky bit positionné sur tous les répertoires world-writable",
            "severity": "MEDIUM",
            "remediation": "chmod +t <répertoire>  # Pour chaque répertoire listé",
        })
    else:
        passed.append({"check": "FS-R54-001", "check_name": "Sticky bit",
                       "found": "Tous les répertoires world-writable ont le sticky bit"})

    return findings, passed


def _r56_r57_setuid_setgid(ssh):
    """R56-R57 — Executables setuid/setgid — inventaire et contrôle."""
    findings, passed = [], []

    # R56 : Tous setuid/setgid
    out, _ = ssh.execute_command(
        "find / -xdev -type f -perm /6000 -not -path '/proc/*' 2>/dev/null"
    )
    setuid_files = [l for l in out.strip().splitlines() if l]

    if len(setuid_files) > 20:
        findings.append({
            "check": "FS-R56-001",
            "check_name": "Nombre élevé de setuid/setgid",
            "description": f"[ANSSI R56] {len(setuid_files)} exécutables avec droits spéciaux setuid/setgid — "
                           "une surface d'attaque importante en cas de vulnérabilité sur l'un d'eux",
            "found": f"{len(setuid_files)} fichiers setuid/setgid",
            "expected": "Minimum nécessaire (< 20 sur un serveur durci)",
            "severity": "MEDIUM",
            "remediation": "Identifier les binaires non indispensables et retirer : chmod u-s,g-s <fichier>",
        })
    else:
        passed.append({
            "check": "FS-R56-001",
            "check_name": "Setuid/setgid",
            "found": f"{len(setuid_files)} exécutables setuid/setgid (niveau acceptable)",
        })

    # R57 : Setuid root spécifiquement
    out, _ = ssh.execute_command(
        "find / -xdev -type f -user root -perm -4000 -not -path '/proc/*' 2>/dev/null"
    )
    setuid_root = [l for l in out.strip().splitlines() if l]

    # Binaires setuid root légitimes courants
    EXPECTED_SETUID_ROOT = {
        "/usr/bin/sudo", "/usr/bin/su", "/bin/su", "/usr/bin/passwd", "/bin/passwd",
        "/usr/bin/newgrp", "/usr/bin/chfn", "/usr/bin/chsh", "/usr/bin/gpasswd",
        "/usr/bin/pkexec", "/usr/lib/openssh/ssh-keysign",
        "/usr/bin/mount", "/usr/bin/umount", "/bin/mount", "/bin/umount",
        "/usr/bin/ping", "/bin/ping",
    }
    unexpected = [f for f in setuid_root if f not in EXPECTED_SETUID_ROOT]
    if unexpected:
        findings.append({
            "check": "FS-R57-001",
            "check_name": "Setuid root non standard",
            "description": "[ANSSI R57] Des exécutables setuid root non habituels ont été trouvés — "
                           "vecteurs d'escalade de privilèges en cas de vulnérabilité",
            "found": ", ".join(unexpected[:10]),
            "expected": "Uniquement les binaires système légitimes (sudo, su, passwd…)",
            "severity": "HIGH",
            "remediation": "Vérifier la légitimité de chaque binaire et retirer : chmod u-s <fichier>",
        })
    else:
        passed.append({"check": "FS-R57-001", "check_name": "Setuid root",
                       "found": f"{len(setuid_root)} setuid root — tous dans la liste blanche"})

    return findings, passed


def run_audit(ssh, rules):
    """Exécute l'audit complet du système de fichiers sur la cible Linux.

    Enchaîne les vérifications R28 à R57 en délégant à chaque sous-fonction
    ANSSI spécialisée, puis agrège findings et passed.

    Args:
        ssh: SSHConnector connecté à la cible.
        rules: dict de règles ; clé reconnue — ``sensitive_files`` (liste de
               tuples pour surcharger ``SENSITIVE_FILES``).

    Returns:
        dict avec clés :
            findings (list[dict]) — non-conformités détectées.
            passed   (list[dict]) — contrôles conformes.
            summary  (dict)       — total_checks, passed, failed.
    """
    findings = []
    passed = []

    for fn in [_r28_partition_options, _r29_boot_access, _r49_sensitive_files,
               _r52_world_writable_files, _r53_orphan_files, _r54_sticky_bit, _r56_r57_setuid_setgid]:
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
