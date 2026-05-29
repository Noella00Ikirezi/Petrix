# un module pour auditer les utilisateurs sur tous les systèmes d'exploitation

# Ce module vérifie les éléments suivants :
# - Les utilisateurs avec des UID inférieurs à 1000 (sauf root)
# - Les utilisateurs sans mot de passe
# - Les utilisateurs avec des shells de connexion non valides  
# Les résultats sont classés en "findings" et "passed" pour faciliter l'analyse.

#windows system
def run_audit(ssh, rules):
    findings = []
    passed = []

    # Vérification des utilisateurs avec UID inférieur à 1000 (sauf root)
    output, error = ssh.execute_command("awk -F: '$3 < 1000 && $1 != \"root\" {print $1}' /etc/passwd")

    if output.strip():
        findings.append({"check": "UID < 1000", "found": output.strip(), "severity": "HIGH"})
    else:
        passed.append({"check": "UID < 1000", "found": "Aucun utilisateur trouvé avec UID inférieur à 1000 (sauf root)"})

    
    # Vérification des utilisateurs sans mot de passe
    output, error = ssh.execute_command("awk -F: '$2 == \"*\" || $2 == \"!\" {print $1}' /etc/shadow")

    if output.strip():
        findings.append({"check": "Users without password", "found": output.strip(), "severity": "HIGH"})
    else:
        passed.append({"check": "Users without password", "found": "Aucun utilisateur sans mot de passe trouvé"})

    # Vérification des shells non valides
    valid_shells = ["/bin/bash", "/bin/sh", "/bin/zsh"]
    output, error = ssh.execute_command("awk -F: '$7 !~ /^\\/bin\\/bash$/ && $7 !~ /^\\/bin\\/sh$/ && $7 !~ /^\\/bin\\/zsh$/ {print $1\":\"$7}' /etc/passwd")

    if output.strip():
        findings.append({"check": "Invalid shells", "found": output.strip(), "severity": "MEDIUM"})
    else:
        passed.append({"check": "Invalid shells", "found": "Tous les shells sont valides"})

#linux system




    return {
        "findings": findings,
        "passed": passed,
        "summary": {
            "total_checks": len(findings) + len(passed),
            "passed": len(passed),
            "failed": len(findings),
        }
    }