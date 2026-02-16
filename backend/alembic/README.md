# Alembic — Migrations de base de données

Gestion des migrations de schéma PostgreSQL avec Alembic.

## Migrations

| Version | Fichier | Description |
|---------|---------|-------------|
| 001 | `001_initial_schema.py` | Schéma initial (users, assets, vulnerabilities, scans, audit_logs) |
| 002 | `002_add_directive_document_type.py` | Ajout du type de document directive |
| 003 | `003_add_pack_type_column.py` | Ajout de la colonne pack_type |
| 004 | `004_add_pentest_tables.py` | Tables PentestAI (targets, sessions, findings, MITRE) |

## Commandes

```bash
# Appliquer toutes les migrations
docker compose exec backend alembic upgrade head

# Créer une nouvelle migration
docker compose exec backend alembic revision --autogenerate -m "description"

# Voir le statut
docker compose exec backend alembic current

# Revenir en arrière (1 migration)
docker compose exec backend alembic downgrade -1
```

## Note

En développement, les tables sont aussi créées automatiquement par `Base.metadata.create_all()` dans `main.py` au démarrage. Les migrations Alembic sont utilisées pour les changements de schéma en production.
