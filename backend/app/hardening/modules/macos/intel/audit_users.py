# Module d'audit : vérifie les comptes utilisateurs macOS Intel via Directory Services (dscl)

def run_audit(ssh, rules):
    findings = []
    passed = []

    # Comptes système avec UID entre 1 et 499 (hors root)
    output, _ = ssh.execute_command(
        "dscl . -list /Users UniqueID | awk '$2+0 > 0 && $2+0 < 500 {print $1, $2}'"
    )
    if output.strip():
        findings.append({"check": "System UID accounts (1-499)", "found": output.strip(), "severity": "MEDIUM"})
    else:
        passed.append({"check": "System UID accounts (1-499)", "found": "Aucun compte système inattendu"})

    # Vérification que le compte Guest est désactivé
    output, _ = ssh.execute_command("dscl . -read /Users/Guest UserShell 2>/dev/null | awk '{print $2}'")
    shell = output.strip()
    if shell and shell not in ("/usr/bin/false", "/sbin/nologin", ""):
        findings.append({"check": "Guest account", "found": f"shell={shell}",
                         "expected": "disabled (/usr/bin/false)", "severity": "HIGH"})
    else:
        passed.append({"check": "Guest account", "found": "disabled"})

    # Shells non valides
    output, _ = ssh.execute_command(
        "dscl . -list /Users UserShell | "
        "awk '$2 !~ /^\\/(bin\\/(bash|sh|zsh)|usr\\/bin\\/false|sbin\\/nologin)$/ {print $1\": \"$2}'"
    )
    if output.strip():
        findings.append({"check": "Shells non valides", "found": output.strip(), "severity": "MEDIUM"})
    else:
        passed.append({"check": "Shells non valides", "found": "Tous les shells sont conformes"})

    return {
        "findings": findings,
        "passed": passed,
        "summary": {
            "total_checks": len(findings) + len(passed),
            "passed": len(passed),
            "failed": len(findings),
        }
    }
