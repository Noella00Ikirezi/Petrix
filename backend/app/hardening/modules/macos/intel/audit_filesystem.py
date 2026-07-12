"""Module d'audit des permissions de fichiers sensibles sur macOS Intel.

Vérifie le mode et le propriétaire des fichiers critiques (/etc/passwd,
/etc/sudoers, sshd_config) via la syntaxe BSD de ``stat`` (``stat -f``),
différente de la syntaxe GNU Linux (``stat -c``).
"""


def run_audit(ssh, rules):
    """Audite les permissions des fichiers sensibles sur macOS Intel.

    Accepte la liste de fichiers à vérifier soit via ``rules["sensitive_files"]``
    (liste de dicts ou de tuples) soit via la liste interne ``SENSITIVE_FILES``.

    Args:
        ssh: SSHConnector connecté à la cible.
        rules: dict de règles ; clé reconnue — ``sensitive_files`` (liste de
               dicts ``{path, mode, owner, group}`` ou de tuples
               ``(path, mode, owner, group)``).

    Returns:
        dict avec clés :
            findings (list[dict]) — permissions ou propriétaires incorrects.
            passed   (list[dict]) — fichiers conformes.
            summary  (dict)       — total_checks, passed, failed.
    """
    findings = []
    passed = []

    SENSITIVE_FILES = [
        ("/etc/passwd",  "644", "root", "wheel"),
        ("/etc/sudoers", "440", "root", "wheel"),
        ("/private/etc/ssh/sshd_config", "644", "root", "wheel"),
    ]

    file_checks = rules.get("sensitive_files", SENSITIVE_FILES)

    for entry in file_checks:
        if isinstance(entry, dict):
            path           = entry["path"]
            expected_mode  = entry.get("mode", "644")
            expected_owner = entry.get("owner", "root")
            expected_group = entry.get("group", "wheel")
        else:
            path, expected_mode, expected_owner, expected_group = entry

        # Permissions (macOS stat BSD syntax: stat -f '%OLp')
        out, _ = ssh.execute_command(f"stat -f '%OLp' {path} 2>/dev/null")
        mode = out.strip()
        if mode != expected_mode:
            findings.append({"check": f"Permissions {path}", "found": mode or "not found",
                             "expected": expected_mode, "severity": "HIGH"})
        else:
            passed.append({"check": f"Permissions {path}", "found": mode})

        # Propriétaire
        out, _ = ssh.execute_command(f"stat -f '%Su' {path} 2>/dev/null")
        owner = out.strip()
        if owner != expected_owner:
            findings.append({"check": f"Owner {path}", "found": owner or "not found",
                             "expected": expected_owner, "severity": "HIGH"})
        else:
            passed.append({"check": f"Owner {path}", "found": owner})

    return {
        "findings": findings,
        "passed": passed,
        "summary": {
            "total_checks": len(findings) + len(passed),
            "passed": len(passed),
            "failed": len(findings),
        }
    }
