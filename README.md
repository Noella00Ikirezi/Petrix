# Petrix

Plateforme de Gouvernance, Risque et Conformité unifiée. Gestion des actifs, vulnérabilités, scans de sécurité, pentests automatisés avec IA, génération de documentation SMSI et suivi de conformité client.

## Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Frontend   │────▶│   Backend    │────▶│  PostgreSQL  │
│  React/Vite  │     │   FastAPI    │     │   (pg 16)    │
│  :5173       │     │   :8000      │     │   :5432      │
└──────────────┘     └──────┬───────┘     └──────────────┘
                            │
                     ┌──────┴───────┐
                     │    Redis     │
                     │   :6379      │
                     └──────┬───────┘
                            │
                     ┌──────┴───────┐     ┌──────────────┐
                     │   Celery     │────▶│    Ollama     │
                     │   Worker     │     │  LLM (local) │
                     │              │     │  :11434      │
                     └──────┬───────┘     └──────────────┘
                            │
                     ┌──────┴───────┐
                     │    MinIO     │
                     │  S3 storage  │
                     │  :9000/:9001 │
                     └──────────────┘
```

**7 services Docker** orchestrés par `docker-compose.yml` :

| Service | Image | Port | Rôle |
|---------|-------|------|------|
| `db` | postgres:16-alpine | 5432 | Base de données relationnelle |
| `redis` | redis:7-alpine | 6379 | Cache + broker Celery |
| `backend` | Build local | 8000 | API REST FastAPI |
| `celery` | Build local | — | Worker asynchrone (scans, IA, rapports) |
| `frontend` | Build local | 5173 | Interface React/Vite |
| `ollama` | ollama/ollama | 11434 | Serveur LLM auto-hébergé |
| `minio` | minio/minio | 9000/9001 | Stockage objet S3-compatible |

## Stack technique

| Couche | Technologies |
|--------|-------------|
| **Backend** | Python 3.11, FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2 |
| **Frontend** | React 18, TypeScript, Vite 5, TailwindCSS 3, TanStack Query, Zustand |
| **Auth** | JWT (HS256) + bcrypt, RBAC 4 rôles / 80+ permissions |
| **Async** | Celery + Redis (broker + backend) |
| **IA** | Ollama (qwen2:0.5b par défaut), httpx sync client |
| **Stockage** | MinIO (rapports pentest HTML/PDF/JSON) |
| **Scans** | python-nmap, Paramiko (SSH) |
| **Rapports** | Jinja2 + WeasyPrint (HTML → PDF) |
| **Charts** | Recharts |
| **Tests** | Pytest, Vitest, Testing Library |

## Modules fonctionnels

### Assets
Inventaire des actifs informatiques (serveurs, workstations, réseau, cloud, conteneurs, IoT). CRUD complet avec catégorisation par type et statut.

### Vulnérabilités
Suivi du cycle de vie des vulnérabilités : détection, analyse, remédiation, vérification. Lié aux actifs et aux scans.

### Scans
Lancement et suivi de scans de sécurité avec résultats intégrés au module vulnérabilités.

### PentestAI
Module de pentest automatisé avec pipeline complet :
1. **Scan réseau** — Nmap (ports, services, OS)
2. **Audit SSH** — Configuration, chiffrement, clés
3. **Audit système** — Fichiers sensibles, permissions, utilisateurs
4. **Mapping MITRE ATT&CK** — Classification des findings par techniques
5. **Enrichissement IA** — Remédiations, résumé exécutif, scénarios d'attaque via Ollama

Pipeline asynchrone Celery avec 3 tasks : `run_pentest_session`, `enrich_pentest_findings`, `generate_pentest_report`.

### Générateur SMSI
Génération automatique de documentation ISO 27001 : politiques de sécurité, procédures, analyses de risques. Templates complets avec export.

### Clients & Conformité
Gestion des clients avec évaluation de conformité, exigences, preuves et remédiation assistée.

### Dashboard
Vue d'ensemble avec métriques clés, répartition des vulnérabilités par sévérité, graphiques Recharts.

## Démarrage rapide

### Prérequis

- Docker & Docker Compose
- 4 Go RAM minimum (Ollama utilise ~500 Mo avec qwen2:0.5b)

### Installation

```bash
# 1. Cloner le projet
git clone <repo-url> petrix
cd petrix

# 2. Configurer les variables d'environnement
cp .env.example .env
# Éditer .env avec des valeurs sécurisées (SECRET_KEY, mots de passe)

# 3. Lancer les services
make dev
# ou directement :
docker compose up -d --build

# 4. (Optionnel) Peupler avec des données de test
make seed
```

### URLs

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| MinIO Console | http://localhost:9001 |

### Credentials par défaut

- **Email** : `admin@petrix.local`
- **Mot de passe** : valeur de `ADMIN_PASSWORD` dans `.env` (défaut : `admin123`)

## Configuration

### Variables d'environnement

| Variable | Description | Défaut |
|----------|-------------|--------|
| `POSTGRES_USER` | Utilisateur PostgreSQL | `petrix` |
| `POSTGRES_PASSWORD` | Mot de passe PostgreSQL | — |
| `POSTGRES_DB` | Nom de la base | `petrix` |
| `SECRET_KEY` | Clé secrète JWT | auto-générée |
| `DEBUG` | Mode debug | `true` |
| `CORS_ORIGINS` | Origines CORS autorisées | `http://localhost:5173,http://localhost:3000` |
| `ADMIN_PASSWORD` | Mot de passe admin initial | `admin123` |
| `OLLAMA_API_URL` | URL du serveur Ollama | `http://ollama:11434` |
| `OLLAMA_MODEL` | Modèle LLM à utiliser | `qwen2:0.5b` |
| `MINIO_ROOT_USER` | Utilisateur MinIO | — |
| `MINIO_ROOT_PASSWORD` | Mot de passe MinIO | — |
| `MINIO_ENDPOINT` | Endpoint MinIO | `minio:9000` |
| `ANTHROPIC_API_KEY` | Clé API Anthropic (optionnel) | — |

### Configuration Pentest

| Variable | Description | Défaut |
|----------|-------------|--------|
| `PENTEST_NMAP_DEFAULT_PORTS` | Ports scannés par défaut | 20 ports courants |
| `PENTEST_NMAP_TIMING` | Timing Nmap | `T4` |
| `PENTEST_MAX_SCAN_DURATION` | Durée max scan (sec) | `3600` |
| `PENTEST_AI_MAX_FINDINGS` | Findings max enrichis par IA | `15` |
| `PENTEST_SSH_TIMEOUT` | Timeout SSH (sec) | `30` |

## API

Tous les endpoints sont préfixés par `/api/v1`. Authentification par token JWT (`Authorization: Bearer <token>`).

### Endpoints par module

| Module | Préfixe | Endpoints principaux |
|--------|---------|---------------------|
| **Auth** | `/auth` | `POST /login`, `POST /register`, `GET /me` |
| **Users** | `/users` | CRUD utilisateurs, gestion des rôles |
| **Assets** | `/assets` | CRUD actifs, recherche, filtres |
| **Vulnérabilités** | `/vulnerabilities` | CRUD vulnérabilités, liaison actifs/scans |
| **Scans** | `/scans` | CRUD scans, lancement, résultats |
| **Dashboard** | `/dashboard` | Métriques, statistiques globales |
| **SMSI** | `/smsi` | Projets, documents, génération, export |
| **Clients** | `/clients` | CRUD clients, exigences, conformité |
| **Pentest** | `/pentest` | Targets, sessions, findings, IA, rapports |
| **System** | `/system` | Info système, health, audit logs |

### Détail API Pentest

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `POST` | `/pentest/targets` | Créer une cible |
| `GET` | `/pentest/targets` | Lister les cibles |
| `DELETE` | `/pentest/targets/{id}` | Supprimer une cible |
| `POST` | `/pentest/sessions` | Lancer un pentest |
| `GET` | `/pentest/sessions` | Lister les sessions |
| `GET` | `/pentest/sessions/{id}` | Détail d'une session |
| `POST` | `/pentest/sessions/{id}/cancel` | Annuler une session |
| `GET` | `/pentest/sessions/{id}/findings` | Findings d'une session |
| `GET` | `/pentest/sessions/{id}/attack-path` | Chemin d'attaque MITRE |
| `POST` | `/pentest/sessions/{id}/report` | Générer un rapport |
| `POST` | `/pentest/ai/enrich` | Enrichir les findings par IA |
| `POST` | `/pentest/ai/remediation/{id}` | Remédiation IA pour un finding |
| `GET` | `/pentest/stats` | Statistiques pentest |

## RBAC — Rôles et permissions

| Rôle | Description | Exemples de permissions |
|------|-------------|----------------------|
| `VIEWER` | Lecture seule | Voir assets, vulns, scans, dashboard |
| `ANALYST` | Analyste sécurité | + Créer/modifier vulns, scans, pentests |
| `AUDITOR` | Auditeur | + Gérer conformité, exporter, générer SMSI |
| `ADMIN` | Administrateur | Toutes les permissions (users, settings, système) |

## Scripts

| Script | Commande | Description |
|--------|----------|-------------|
| `seed_test_data` | `make seed` | Peuple la DB avec des données de test |
| `seed_smsi_data` | Via backend | Injecte les templates SMSI ISO 27001 |
| `install.sh` | `bash scripts/install.sh` | Installation production (Ubuntu/Debian/RHEL) |

## Tests

```bash
# Backend — tests unitaires
docker compose exec backend pytest

# Frontend — tests unitaires
docker compose exec frontend npm test

# Environnement de test isolé
make test
```

Tests backend : `conftest.py` (fixtures DB), `test_config.py`, `test_health.py`, `test_licensing.py`, `test_permissions.py`, `test_security.py`.

## Commandes Make

| Commande | Description |
|----------|-------------|
| `make dev` | Lancer l'environnement de développement |
| `make dev-build` | Rebuild + lancer |
| `make dev-down` | Arrêter l'environnement |
| `make dev-logs` | Logs en temps réel |
| `make test` | Lancer l'environnement de test |
| `make test-run` | Exécuter les tests |
| `make seed` | Peupler la DB de dev |
| `make shell-backend` | Shell dans le container backend |
| `make shell-db` | psql dans le container DB |
| `make status` | Status de tous les containers |
| `make clean` | Arrêter tous les environnements |
| `make clean-all` | Tout supprimer (containers, volumes, images) |

## Structure du projet

```
petrix/
├── backend/
│   ├── app/
│   │   ├── api/v1/              # Endpoints REST (10 modules)
│   │   │   ├── router.py        # Routeur principal
│   │   │   ├── deps.py          # Dépendances auth/permissions
│   │   │   ├── auth.py          # Login, register
│   │   │   ├── users.py         # Gestion utilisateurs
│   │   │   ├── assets.py        # Gestion actifs
│   │   │   ├── vulnerabilities.py
│   │   │   ├── scans.py
│   │   │   ├── dashboard.py
│   │   │   ├── system.py
│   │   │   ├── smsi.py
│   │   │   ├── clients.py
│   │   │   └── pentest.py       # API PentestAI complète
│   │   ├── core/                # Sécurité et RBAC
│   │   │   ├── security.py      # JWT + bcrypt
│   │   │   └── permissions.py   # 4 rôles, 80+ permissions
│   │   ├── infrastructure/
│   │   │   └── database/        # Modèles SQLAlchemy
│   │   │       ├── models.py    # User, Asset, Vulnerability, Scan, AuditLog
│   │   │       ├── pentest_models.py  # PentestTarget, AuditSession, PentestFinding
│   │   │       ├── smsi_models.py     # Documents SMSI
│   │   │       └── client_requirements_models.py
│   │   ├── application/
│   │   │   ├── smsi/            # Générateur SMSI (10 fichiers)
│   │   │   └── compliance/      # Service de remédiation
│   │   ├── pentest/             # Module PentestAI
│   │   │   ├── scanners/        # NmapScanner
│   │   │   ├── auditors/        # SSHAuditor, SystemAuditor, base
│   │   │   ├── analyzers/       # MitreMapper
│   │   │   ├── ai/              # PentestAIClient, prompts
│   │   │   ├── reports/         # PentestReportGenerator + templates
│   │   │   ├── schemas/         # Pydantic v2 schemas
│   │   │   └── services/
│   │   ├── schemas/             # Schemas partagés
│   │   ├── workers/             # Celery tasks
│   │   │   ├── celery_app.py
│   │   │   └── pentest_tasks.py
│   │   ├── config.py            # Settings Pydantic
│   │   └── main.py              # Point d'entrée FastAPI
│   ├── alembic/                 # Migrations DB
│   │   └── versions/            # 4 migrations
│   ├── scripts/                 # Seed data
│   ├── tests/                   # Tests unitaires
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/client.ts        # Client API Axios + helpers
│   │   ├── stores/authStore.ts  # Store Zustand (auth)
│   │   ├── pages/               # Pages par module
│   │   │   ├── DashboardPage.tsx
│   │   │   ├── auth/LoginPage.tsx
│   │   │   ├── assets/AssetsPage.tsx
│   │   │   ├── vulnerabilities/VulnerabilitiesPage.tsx
│   │   │   ├── scans/ScansPage.tsx
│   │   │   ├── smsi/SMSIPage.tsx
│   │   │   ├── clients/ClientsPage.tsx
│   │   │   ├── users/UsersPage.tsx
│   │   │   ├── settings/SettingsPage.tsx
│   │   │   └── pentest/
│   │   │       ├── PentestPage.tsx
│   │   │       ├── PentestSessionDetail.tsx
│   │   │       └── types.ts
│   │   ├── components/          # Composants réutilisables
│   │   │   ├── layout/          # Layout, Header, Sidebar
│   │   │   ├── clients/         # 6 composants clients
│   │   │   └── smsi/            # 7 composants SMSI
│   │   └── utils/               # Utilitaires (markdown converter)
│   ├── Dockerfile
│   └── package.json
├── scripts/
│   └── install.sh               # Script d'installation production
├── legacy/                      # Projets archivés
│   ├── grc-agent/
│   ├── secop/
│   └── superassistant/
├── docker-compose.yml           # Orchestration 7 services
├── docker-compose.test.yml      # Environnement de test isolé
├── Makefile                     # Commandes pratiques
├── .env.example                 # Template variables d'environnement
└── README.md                    # Ce fichier
```

## Développement local (sans Docker)

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# Lancer PostgreSQL et Redis via Docker :
docker compose up -d db redis
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

## Licence

Projet propriétaire — Certix.
