"""Module d'audit du pare-feu ALF (Application Layer Firewall) macOS Intel.

Vérifie l'état d'activation du pare-feu applicatif macOS via ``defaults``
et ``socketfilterfw``. Module en cours d'implémentation (stub fonctionnel).
"""


def run_audit(ssh, rules):
    """Audite le pare-feu ALF macOS Intel (stub — implémentation à compléter).

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

    # TODO: vérifier l'état du pare-feu ALF macOS
    # Exemples de commandes :
    #   defaults read /Library/Preferences/com.apple.alf globalstate
    #     0 = désactivé, 1 = activé pour les applications approuvées, 2 = mode furtif
    #   /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate

    return {
        "findings": findings,
        "passed": passed,
        "summary": {
            "total_checks": len(findings) + len(passed),
            "passed": len(passed),
            "failed": len(findings),
        }
    }
