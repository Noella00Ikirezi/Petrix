# Discovery Audit

Outil d'audit de sécurité en mode discovery - Explore automatiquement l'environnement et génère un rapport détaillé avec notation.

## Installation

```bash
cd /Users/nikirezi/Documents/Server/05-grc-agent
pip install -e .
```

### Dépendances optionnelles (recommandées)

```bash
# Scanner réseau avancé
brew install nmap

# Scanner web avancé
go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
```

## Utilisation

### Commandes principales

```bash
# Voir l'aide
python3 -m discovery_audit.cli --help

# Audit d'une ou plusieurs cibles
python3 -m discovery_audit.cli scan 192.168.1.1
python3 -m discovery_audit.cli scan example.com https://api.example.com
python3 -m discovery_audit.cli scan 192.168.1.0/24

# Audit du système local uniquement
python3 -m discovery_audit.cli local

# Voir les modules disponibles
python3 -m discovery_audit.cli info

# Régénérer un rapport depuis un JSON existant
python3 -m discovery_audit.cli report audit.json -f html
```

### Options de scan

| Option | Description |
|--------|-------------|
| `-n, --name` | Nom de l'audit |
| `-o, --output` | Répertoire de sortie (défaut: ./reports) |
| `-p, --ports` | Ports à scanner (1-1000, full, 22,80,443) |
| `-A, --aggressive` | Mode agressif (OS detection, scripts) |
| `--no-network` | Désactiver le scan réseau |
| `--no-system` | Désactiver l'audit système |
| `--no-web` | Désactiver l'audit web |
| `--no-vuln` | Désactiver le scan de vulnérabilités |
| `--json` | Générer uniquement le rapport JSON |
| `--html` | Générer uniquement le rapport HTML |
| `-t, --timeout` | Timeout total en secondes |

### Exemples

```bash
# Scan complet d'un réseau
python3 -m discovery_audit.cli scan 192.168.1.0/24 -n "Audit Réseau Prod" -o ./rapports

# Scan agressif avec tous les ports
python3 -m discovery_audit.cli scan 10.0.0.1 -p full -A

# Audit web uniquement
python3 -m discovery_audit.cli scan https://example.com --no-network --no-system

# Export JSON uniquement (pour intégration CI/CD)
python3 -m discovery_audit.cli scan 192.168.1.1 --json
```

## Architecture

```
discovery-audit/
├── config/
│   └── default.yaml          # Configuration par défaut
├── src/discovery_audit/
│   ├── cli.py                # Interface ligne de commande
│   ├── core/
│   │   ├── engine.py         # Orchestrateur principal
│   │   ├── models.py         # Modèles de données
│   │   └── scoring.py        # Système de notation
│   ├── modules/
│   │   ├── network_scanner.py  # Scan réseau (Nmap)
│   │   ├── system_auditor.py   # Audit système Linux/Windows
│   │   ├── web_scanner.py      # Scan web (Nuclei)
│   │   └── vuln_scanner.py     # Détection CVE
│   └── reports/
│       └── generator.py      # Génération HTML/PDF/JSON
└── reports/                  # Rapports générés
```

## Modules

### Network Scanner
- Scan de ports TCP/UDP
- Détection de services et versions
- Détection d'OS
- Intégration Nmap (avec fallback Python)

### System Auditor
- Configuration SSH
- Permissions sudo
- Fichiers world-writable
- Binaires SUID/SGID
- Configuration firewall
- Mises à jour de sécurité
- Services dangereux
- Utilisateurs et groupes

### Web Scanner
- Headers de sécurité (HSTS, CSP, X-Frame-Options...)
- Configuration SSL/TLS
- Fichiers sensibles exposés (.git, .env, backups...)
- Directory listing
- Méthodes HTTP dangereuses
- Cookies de session
- Intégration Nuclei

### Vulnerability Scanner
- Base de CVE connues
- Détection de versions obsolètes
- Services mal configurés (Redis, MongoDB, Elasticsearch...)
- Enrichissement avec informations d'exploit

## Système de Notation

### Grades

| Grade | Score | Description |
|-------|-------|-------------|
| A | 90-100 | Excellente posture de sécurité |
| B | 75-89 | Bonne posture avec améliorations mineures |
| C | 60-74 | Posture moyenne, remédiation recommandée |
| D | 40-59 | Posture faible, action requise |
| F | 0-39 | Posture critique, action urgente |

### Sévérités

| Sévérité | Impact sur le score |
|----------|---------------------|
| Critical | -40 points |
| High | -25 points |
| Medium | -10 points |
| Low | -3 points |
| Info | 0 points |

## Rapports

Les rapports sont générés dans le dossier `./reports` (configurable) :

- **HTML** : Rapport interactif avec graphiques
- **PDF** : Rapport imprimable
- **JSON** : Export pour intégration CI/CD

## Configuration

Modifier `config/default.yaml` pour personnaliser :

```yaml
# Phases activées
enable_network_scan: true
enable_system_audit: true
enable_web_audit: true
enable_vuln_scan: true

# Ports à scanner
network:
  ports: "1-1000"
  scan_udp: false
  aggressive: false

# Timeouts
timeouts:
  per_host: 300
  total: 3600
```

## Roadmap

- [ ] Dashboard web temps réel
- [ ] Intégration Active Directory
- [ ] Audit cloud (AWS/Azure/GCP)
- [ ] API REST
- [ ] Intégration Jira/Slack
- [ ] Scan de conteneurs Docker
- [ ] Compliance (ISO 27001, PCI-DSS, RGPD)

## Licence

Propriétaire - Afluens
