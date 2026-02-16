# Workers — Celery Tasks

Worker Celery asynchrone pour les tâches longues (scans pentest, enrichissement IA, génération de rapports).

## Structure

```
workers/
├── __init__.py          # Re-export celery_app
├── celery_app.py        # Configuration Celery (broker Redis, serialization JSON)
└── pentest_tasks.py     # 3 tasks pentest
```

## Configuration (`celery_app.py`)

- **Broker** : Redis (`redis://redis:6379/0`)
- **Backend** : Redis
- **Sérialisation** : JSON
- **Concurrency** : 2 workers (configurable)

## Tasks

| Task | Description | Déclencheur |
|------|-------------|-------------|
| `run_pentest_session` | Exécute le pipeline complet (scan → audit → MITRE → IA → rapport) | `POST /pentest/sessions` |
| `enrich_pentest_findings` | Enrichit les findings existants avec IA (remédiations, résumé) | `POST /pentest/ai/enrich` |
| `generate_pentest_report` | Génère un rapport HTML/PDF/JSON et l'uploade sur MinIO | `POST /pentest/sessions/{id}/report` |

## Docker

Le worker Celery tourne dans un container séparé (`petrix-celery`) avec :
- `user: root` et `cap_add: [NET_RAW, NET_ADMIN]` pour les scans Nmap
- Accès à Ollama (`OLLAMA_API_URL`) et MinIO (`MINIO_ENDPOINT`)
- Même image que le backend (partage le code)

```bash
# Commande de lancement
celery -A app.workers.celery_app worker --loglevel=info --concurrency=2
```
