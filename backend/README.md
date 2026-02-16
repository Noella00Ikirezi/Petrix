# Backend — Petrix

API REST FastAPI pour la Petrix. Gère l'authentification, le RBAC, les modèles de données et tous les services métier.

## Structure

```
backend/
├── app/
│   ├── main.py              # Point d'entrée FastAPI (lifespan, CORS, admin auto)
│   ├── config.py             # Settings Pydantic (toutes les env vars)
│   ├── api/v1/               # Endpoints REST — 10 modules
│   ├── core/                 # Sécurité (JWT/bcrypt) et RBAC (4 rôles)
│   ├── infrastructure/       # Modèles SQLAlchemy et connexion DB
│   ├── application/          # Services métier (SMSI, compliance)
│   ├── pentest/              # Module PentestAI complet
│   ├── schemas/              # Schemas Pydantic partagés
│   └── workers/              # Celery tasks (pentest async)
├── alembic/                  # Migrations de base de données
├── scripts/                  # Scripts seed et utilitaires
├── tests/                    # Tests unitaires (Pytest)
├── Dockerfile
└── requirements.txt
```

## Démarrage

```bash
# Via Docker (recommandé)
docker compose up -d backend

# Développement local
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Modèles de données

### Core (`models.py`)
- **User** — Utilisateur avec rôle RBAC et hachage bcrypt
- **Asset** — Actif informatique (type, statut, criticité)
- **Vulnerability** — Vulnérabilité liée à un actif (sévérité, statut, CVE)
- **Scan** — Scan de sécurité (type, statut, résultats)
- **AuditLog** — Journal d'audit des actions utilisateur

### Pentest (`pentest_models.py`)
- **PentestTarget** — Cible SSH (host, port, credentials chiffrés)
- **AuditSession** — Session de pentest (statut, progression, score de risque)
- **PentestFinding** — Découverte de sécurité (sévérité, MITRE, remédiation)
- **MitreTechnique** — Technique MITRE ATT&CK référencée

### SMSI (`smsi_models.py`)
- Projets et documents SMSI ISO 27001

### Clients (`client_requirements_models.py`)
- Clients, exigences de conformité, évaluations

## Variables d'environnement

Toutes les variables sont documentées dans `app/config.py` et dans le README racine.

## API Docs

Swagger UI disponible sur `http://localhost:8000/docs` quand le service tourne.
