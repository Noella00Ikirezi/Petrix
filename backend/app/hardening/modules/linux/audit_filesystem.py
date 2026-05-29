# Module d'audit : vérifie les permissions et propriétaires des fichiers sensibles via SSH

SENSITIVE_FILES = [
    ("/etc/passwd",  "644", "root", "root"),
    ("/etc/shadow",  "640", "root", "shadow"),
    ("/etc/group",   "644", "root", "root"),
    ("/etc/sudoers", "440", "root", "root"),
]

def run_audit(ssh, rules):
    findings = []
    passed = []

    file_checks = rules.get("sensitive_files", SENSITIVE_FILES)

    for entry in file_checks:
        if isinstance(entry, dict):
            path           = entry["path"]
            expected_mode  = entry.get("mode", "644")
            expected_owner = entry.get("owner", "root")
            expected_group = entry.get("group", "root")
        else:
            path, expected_mode, expected_owner, expected_group = entry

        # Permissions en octal (ex: 644)
        out, _ = ssh.execute_command(f"stat -c '%a' {path} 2>/dev/null")
        mode = out.strip()
        if mode != expected_mode:
            findings.append({"check": f"Permissions {path}", "found": mode or "not found",
                             "expected": expected_mode, "severity": "HIGH"})
        else:
            passed.append({"check": f"Permissions {path}", "found": mode})

        # Propriétaire
        out, _ = ssh.execute_command(f"stat -c '%U' {path} 2>/dev/null")
        owner = out.strip()
        if owner != expected_owner:
            findings.append({"check": f"Owner {path}", "found": owner or "not found",
                             "expected": expected_owner, "severity": "HIGH"})
        else:
            passed.append({"check": f"Owner {path}", "found": owner})

        # Groupe
        out, _ = ssh.execute_command(f"stat -c '%G' {path} 2>/dev/null")
        group = out.strip()
        if group != expected_group:
            findings.append({"check": f"Group {path}", "found": group or "not found",
                             "expected": expected_group, "severity": "MEDIUM"})
        else:
            passed.append({"check": f"Group {path}", "found": group})

    return {
        "findings": findings,
        "passed": passed,
        "summary": {
            "total_checks": len(findings) + len(passed),
            "passed": len(passed),
            "failed": len(findings),
        }
    }
