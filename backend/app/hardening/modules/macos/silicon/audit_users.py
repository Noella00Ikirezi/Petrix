"""Module d'audit des comptes utilisateurs macOS Apple Silicon.

Interroge le répertoire local via ``dscl`` pour détecter les comptes système
inattendus, le compte Guest actif et les shells non conformes. Identique au
module Intel ; la séparation permet des extensions arm64-spécifiques futures.
"""


def run_audit(ssh, rules):
    """Audite les comptes utilisateurs macOS Silicon via Directory Services.

    Args:
        ssh: SSHConnector connecté à la cible.
        rules: dict de règles (non utilisé pour ce module).

    Returns:
        dict avec clés :
            findings (list[dict]) — comptes à risque détectés.
            passed   (list[dict]) — contrôles conformes.
            summary  (dict)       — total_checks, passed, failed.
    """
    findings = []
    passed = []

    output, _ = ssh.execute_command(
        "dscl . -list /Users UniqueID | awk '$2+0 > 0 && $2+0 < 500 {print $1, $2}'"
    )
    if output.strip():
        findings.append({"check": "System UID accounts (1-499)", "found": output.strip(), "severity": "MEDIUM"})
    else:
        passed.append({"check": "System UID accounts (1-499)", "found": "Aucun compte système inattendu"})

    output, _ = ssh.execute_command("dscl . -read /Users/Guest UserShell 2>/dev/null | awk '{print $2}'")
    shell = output.strip()
    if shell and shell not in ("/usr/bin/false", "/sbin/nologin", ""):
        findings.append({"check": "Guest account", "found": f"shell={shell}",
                         "expected": "disabled (/usr/bin/false)", "severity": "HIGH"})
    else:
        passed.append({"check": "Guest account", "found": "disabled"})

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
