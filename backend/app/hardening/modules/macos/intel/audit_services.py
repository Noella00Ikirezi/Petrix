# Module d'audit : détecte les services dangereux ou inutiles en cours d'exécution sur macOS

def run_audit(ssh, rules):
    findings = []
    passed = []

    # TODO: vérifier les services via launchctl
    # Exemples de commandes :
    #   launchctl list | grep <service>
    #   launchctl print system/com.apple.ftpd

    return {
        "findings": findings,
        "passed": passed,
        "summary": {
            "total_checks": len(findings) + len(passed),
            "passed": len(passed),
            "failed": len(findings),
        }
    }
