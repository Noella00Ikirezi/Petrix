"""Module d'audit des services macOS Apple Silicon via launchctl.

Stub fonctionnel — même périmètre que le module Intel. L'implémentation
utilisera ``launchctl list`` et ``launchctl print`` pour détecter les services
FTP, partage d'écran et autres services non nécessaires.
"""


def run_audit(ssh, rules):
    """Audite les services macOS Silicon via launchctl (stub — à compléter).

    Args:
        ssh: SSHConnector connecté à la cible.
        rules: dict de règles (non utilisé pour ce module).

    Returns:
        dict avec clés :
            findings (list[dict]) — toujours vide (à implémenter).
            passed   (list[dict]) — toujours vide (à implémenter).
            summary  (dict)       — total_checks=0, passed=0, failed=0.
    """
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
