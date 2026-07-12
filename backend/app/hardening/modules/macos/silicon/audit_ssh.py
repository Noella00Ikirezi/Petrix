"""Module d'audit SSH pour macOS Apple Silicon (M-series, arm64).

Identique au module Intel dans ses contrôles ; la séparation en sous-module
permet d'y ajouter des vérifications spécifiques à l'architecture arm64
(Secure Enclave, T2-équivalent Arm) lors d'itérations futures.
"""


def run_audit(ssh, rules):
    """Audite la configuration sshd_config sur macOS Apple Silicon.

    Args:
        ssh: SSHConnector connecté à la cible.
        rules: dict de règles ; clés reconnues — ``root_login``,
               ``password_auth``, ``challenge_response_auth``,
               ``pubkey_auth``, ``permit_empty_passwords``,
               ``x11_forwarding``, ``max_auth_tries``.

    Returns:
        dict avec clés :
            findings (list[dict]) — directives non conformes.
            passed   (list[dict]) — directives conformes.
            summary  (dict)       — total_checks, passed, failed.
    """
    findings = []
    passed = []

    config = "/etc/ssh/sshd_config"

    # PermitRootLogin
    output, _ = ssh.execute_command(f"grep '^PermitRootLogin' {config} | awk '{{print $2}}'")
    expected = rules.get("root_login", "no").lower()
    found = output.strip().lower()
    if found != expected:
        findings.append({"check": "PermitRootLogin", "found": found or "not set", "expected": expected, "severity": "HIGH"})
    else:
        passed.append({"check": "PermitRootLogin", "found": found})

    # PasswordAuthentication
    output, _ = ssh.execute_command(f"grep '^PasswordAuthentication' {config} | awk '{{print $2}}'")
    expected = rules.get("password_auth", "no").lower()
    found = output.strip().lower()
    if found != expected:
        findings.append({"check": "PasswordAuthentication", "found": found or "not set", "expected": expected, "severity": "HIGH"})
    else:
        passed.append({"check": "PasswordAuthentication", "found": found})

    # ChallengeResponseAuthentication (macOS-specific — désactive l'auth interactive)
    output, _ = ssh.execute_command(f"grep '^ChallengeResponseAuthentication' {config} | awk '{{print $2}}'")
    expected = rules.get("challenge_response_auth", "no").lower()
    found = output.strip().lower()
    if found != expected:
        findings.append({"check": "ChallengeResponseAuthentication", "found": found or "not set", "expected": expected, "severity": "MEDIUM"})
    else:
        passed.append({"check": "ChallengeResponseAuthentication", "found": found})

    # PubkeyAuthentication
    output, _ = ssh.execute_command(f"grep '^PubkeyAuthentication' {config} | awk '{{print $2}}'")
    expected = rules.get("pubkey_auth", "yes").lower()
    found = output.strip().lower() or "yes"  # default is yes
    if found != expected:
        findings.append({"check": "PubkeyAuthentication", "found": found, "expected": expected, "severity": "HIGH"})
    else:
        passed.append({"check": "PubkeyAuthentication", "found": found})

    # PermitEmptyPasswords
    output, _ = ssh.execute_command(f"grep '^PermitEmptyPasswords' {config} | awk '{{print $2}}'")
    expected = rules.get("permit_empty_passwords", "no").lower()
    found = output.strip().lower() or "no"
    if found != expected:
        findings.append({"check": "PermitEmptyPasswords", "found": found, "expected": expected, "severity": "HIGH"})
    else:
        passed.append({"check": "PermitEmptyPasswords", "found": found})

    # X11Forwarding
    output, _ = ssh.execute_command(f"grep '^X11Forwarding' {config} | awk '{{print $2}}'")
    expected = rules.get("x11_forwarding", "no").lower()
    found = output.strip().lower() or "no"
    if found != expected:
        findings.append({"check": "X11Forwarding", "found": found, "expected": expected, "severity": "MEDIUM"})
    else:
        passed.append({"check": "X11Forwarding", "found": found})

    # MaxAuthTries
    output, _ = ssh.execute_command(f"grep '^MaxAuthTries' {config} | awk '{{print $2}}'")
    max_tries = rules.get("max_auth_tries", 4)
    if output.strip():
        try:
            found_val = int(output.strip())
            if found_val > max_tries:
                findings.append({"check": "MaxAuthTries", "found": str(found_val), "expected": f"<= {max_tries}", "severity": "MEDIUM"})
            else:
                passed.append({"check": "MaxAuthTries", "found": str(found_val)})
        except ValueError:
            findings.append({"check": "MaxAuthTries", "found": output.strip(), "expected": f"<= {max_tries}", "severity": "LOW"})
    else:
        passed.append({"check": "MaxAuthTries", "found": "default (6)"})

    return {
        "findings": findings,
        "passed": passed,
        "summary": {
            "total_checks": len(findings) + len(passed),
            "passed": len(passed),
            "failed": len(findings),
        }
    }
