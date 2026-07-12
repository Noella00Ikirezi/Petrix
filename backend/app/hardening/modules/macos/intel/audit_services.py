"""Module d'audit des services macOS Intel via launchctl.

Détecte les services inutiles ou dangereux (FTP, partage d'écran…) exposés
sur la cible macOS Intel. Module en cours d'implémentation (stub fonctionnel).
"""


def run_audit(ssh, rules):
    """Audite les services macOS Intel via launchctl (stub — à compléter).

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
