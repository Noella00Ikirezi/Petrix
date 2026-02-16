# Scripts — Déploiement production

Scripts d'installation et de déploiement pour environnements de production.

## Fichiers

| Script | Description |
|--------|-------------|
| `install.sh` | Script d'installation automatique pour serveurs Linux |

## `install.sh`

Script d'installation complet pour déployer la Petrix en production.

### Systèmes supportés

- Ubuntu 22.04
- Debian 12
- RHEL 9
- Rocky Linux 9

### Utilisation

```bash
sudo bash scripts/install.sh
```

Le script installe les dépendances système, configure Docker, et déploie l'ensemble des services.
