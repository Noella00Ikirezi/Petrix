# Changelog

Tous les changements notables du projet PentestAI.

## [0.1.0] - 2026-01-20

### Ajouté
- Interface CLI moderne avec Typer et Rich
  - Commande `scan` pour scanner des cibles
  - Commande `demo` pour prévisualiser l'interface
  - Bannière ASCII colorée
  - Tableaux et barres de progression
- Interface web FastAPI
  - Dashboard avec authentification
  - API REST pour lancer des scans
  - Gestion des rapports
- Scanner réseau avec python-nmap
  - Découverte d'hôtes
  - Scan de ports (quick et full)
  - Détection de services et versions
- Analyseur MITRE ATT&CK
  - 25+ mappings de vulnérabilités
  - 18 règles de détection par port
  - Génération de chemins d'attaque
- Intégration IA locale (Ollama + Mistral)
  - Génération de remédiations
  - Scénarios d'attaque
  - Explication des techniques MITRE
- Système de sécurité
  - Validation des entrées (IP, ports, paths)
  - Protection contre l'injection de commandes
  - Sanitization des prompts IA
- Authentification et autorisations
  - Gestion des utilisateurs
  - Rôles (Admin, Analyst, Viewer)
  - Sessions avec expiration
  - Audit logging
- Génération de rapports
  - Format HTML avec style moderne
  - Format JSON pour intégration
  - Score de risque (0-10)
- Configuration robuste
  - Fichier .env avec tous les paramètres
  - Validation Pydantic
  - Secrets sécurisés
- Tests unitaires
  - Tests de sécurité
  - Tests du scanner
  - Tests du mapper MITRE
- Documentation complète
  - README avec instructions détaillées
  - Docstrings dans le code
  - Exemples d'utilisation

### Sécurité
- Hachage des mots de passe (PBKDF2-SHA256)
- Politique de mots de passe robuste (12+ chars, complexité)
- Protection contre les injections de commandes nmap
- Sanitization des données avant prompts IA

## Roadmap

### [0.2.0] - Prévu
- [ ] Export PDF des rapports
- [ ] Base de données CVE intégrée
- [ ] Scans programmés (cron)
- [ ] Notifications par email

### [0.3.0] - Prévu
- [ ] Intégration SIEM
- [ ] API webhook
- [ ] Mode multi-tenant
- [ ] Dashboard temps réel
