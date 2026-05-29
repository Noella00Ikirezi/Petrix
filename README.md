# Petrix

Plateforme de Gouvernance, Risque et Conformité (GRC) unifiée. Gestion des actifs, vulnérabilités, scans de sécurité, pentests automatisés avec IA, audit de durcissement (Hardening), génération de documentation SMSI et suivi de conformité client.

**Production** : https://petrix.noellahome.org
**GitLab** : https://gitlab.com/petrix1/petrix

---

## Architecture

```
┌──────────────┐     ┌──────────────┐     ┌─────────────────────┐
│   Frontend   │────▶│   Backend    │────▶│   PostgreSQL (RDS)  │
│  React/Vite  │     │   FastAPI    │     │   :5432             │
│  :5173       │     │   :8000      │     └─────────────────────┘
└──────────────┘     └──────┬───────┘
         ▲                  │
         │            ┌─────┴──────┐     ┌──────────────┐
    [nginx :80]       │   Redis    │────▶│    Celery    │
    (prod only)       │   :6379    │     │    Worker    │
                      └────────────┘     └──────┬───────┘
                                                │
                                         ┌──────┴───────┐
                                         │    MinIO     │
                                         │  :9000/:9001 │
                                         └──────────────┘
```

### Services Docker — dev local

| Service | Image | Port | Rôle |
|---------|-------|------|------|
| `db` | postgres:16-alpine | 5432 | Base de données PostgreSQL |
| `redis` | redis:7-alpine | 6379 | Cache + broker Celery |
| `backend` | Build local | 8000 | API REST FastAPI (hot reload) |
| `celery` | Build local | — | Worker asynchrone |
| `frontend` | Build local | 5173 | Interface React/Vite (HMR) |
| `minio` | minio/minio | 9000/9001 | Stockage objet S3-compatible |
| `mailpit` | axllent/mailpit | 8025/1025 | Intercepteur d'emails (OTP) |
| `adminer` | adminer | 8080 | Navigateur SQL web |

### Services Docker — prod (EC2)

| Service | Rôle |
|---------|------|
| `redis` | Broker Celery |
| `backend` | API FastAPI (2 workers uvicorn) |
| `celery` | Worker asynchrone |
| `frontend` | Vite dev server |
| `nginx` | Reverse proxy :80 → backend :8000 / frontend :5173 |

---

## Stack technique

| Couche | Technologies |
|--------|-------------|
| **Backend** | Python 3.11, FastAPI, SQLAlchemy 2.0, Pydantic v2 |
| **Frontend** | React 18, TypeScript, Vite 5, TailwindCSS 3, TanStack Query, Zustand |
| **Auth** | JWT (HS256) + bcrypt, OTP par email, RBAC 4 rôles / 80+ permissions |
| **Async** | Celery + Redis (broker + backend) |
| **Hardening** | Paramiko (SSH), audits Linux : SSH · Users · Kernel · Firewall · Services |
| **Stockage** | MinIO (rapports, fichiers) |
| **IA** | Groq API / Ollama (optionnel) |
| **Email** | SMTP — Mailpit en dev, SMTP réel en prod |
| **CI/CD** | GitLab CI → deploy automatique sur EC2 (branche `main`) |
| **Infra** | AWS EC2 t3.small eu-west-1, RDS PostgreSQL, Route53 + Cloudflare |

---

## Modules fonctionnels

### Assets
Inventaire des actifs informatiques (serveurs, workstations, réseau, cloud, conteneurs, IoT). CRUD complet avec catégorisation par type et statut.

### Vulnérabilités
Suivi du cycle de vie des vulnérabilités : détection, analyse, remédiation, vérification. Lié aux actifs et aux scans.

### Scans
Lancement et suivi de scans réseau (Nmap) avec résultats intégrés au module vulnérabilités.

### PentestAI
Module de pentest automatisé avec pipeline complet :
1. Scan réseau — Nmap (ports, services, OS)
2. Audit SSH — Configuration, chiffrement, clés
3. Audit système — Fichiers sensibles, permissions, utilisateurs
4. Mapping MITRE ATT&CK — Classification des findings par techniques
5. Enrichissement IA — Remédiations, résumé exécutif via Groq/Ollama

Pipeline Celery : `run_pentest_session` → `enrich_pentest_findings` → `generate_pentest_report`.

### Hardening
Audit de durcissement Linux via SSH. Connexion Paramiko, scoring 0–100 (grades A→F), 5 modules :

| Module | Contrôles |
|--------|-----------|
| `ssh` | PasswordAuth, PermitRootLogin, protocoles, ciphers |
| `users` | Comptes sans mot de passe, UID 0 non-root, sudoers |
| `kernel` | ASLR, sysctl réseau, paramètres de sécurité |
| `firewall` | iptables / nftables / ufw actif |
| `services` | Services inutiles exposés (telnet, rsh, etc.) |

Sessions asynchrones Celery. Findings avec sévérité CRITICAL/HIGH/MEDIUM/LOW et remédiation.

### Générateur SMSI
Génération automatique de documentation ISO 27001 : politiques, procédures, analyses de risques.

### Clients & Conformité
Gestion clients avec évaluation de conformité, exigences, preuves et remédiation assistée.

### Dashboard
Vue d'ensemble avec métriques clés, répartition des vulnérabilités par sévérité, graphiques Recharts.

---

## Démarrage rapide (dev local)

### Prérequis

- Docker Desktop (Mac/Windows) ou Docker Engine (Linux)
- `make`

### Installation

```bash
# 1. Cloner le projet
git clone git@gitlab.com:petrix1/petrix.git
cd petrix

# 2. Configurer les variables d'environnement
cp .env.example .env
# Éditer .env : SECRET_KEY, mots de passe (ne jamais committer .env)
# Générer une SECRET_KEY : openssl rand -hex 32

# 3. Builder et lancer tous les services
make build

# 4. Vérifier que tout est up
make status
```

### URLs dev local

| Service | URL | Credentials |
|---------|-----|-------------|
| **Frontend** | http://localhost:5173 | — |
| **API / Swagger** | http://localhost:8000/docs | — |
| **Adminer** (SQL) | http://localhost:8080 | server: `db`, user: `petrix`, pw: dans `.env` |
| **Mailpit** (emails OTP) | http://localhost:8025 | — |
| **MinIO** (S3) | http://localhost:9001 | `minioadmin` / `minioadmin123` |

**Compte admin** : `admin@petrix.local` / valeur de `ADMIN_PASSWORD` dans `.env`

---

## Commandes Make

```bash
make dev                 # Lancer l'env de dev (hot reload)
make build               # Rebuild les images + lancer
make dev-down            # Arrêter l'env de dev
make logs                # Logs de tous les services (follow)
make dev-logs-backend    # Logs backend uniquement
make dev-logs-celery     # Logs Celery uniquement
make status              # Status de tous les containers
make shell-backend       # Shell bash dans le container backend
make shell-db            # psql dans le container DB
make seed                # Peupler la DB avec des données de test
make clean               # Arrêter tous les services
make clean-all           # Supprimer containers, volumes et images
```

---

## CI/CD — GitLab → EC2

### Pipeline automatique

Sur chaque push vers `main` :

```
lint → test → build → deploy
```

### Variables GitLab à configurer

**GitLab → Settings → CI/CD → Variables** (toutes Protected + Masked) :

| Variable | Valeur |
|----------|--------|
| `EC2_SSH_KEY` | Clé privée ED25519 du deploy key |
| `EC2_HOST` | `3.255.126.244` |
| `EC2_USER` | `ec2-user` |
| `EC2_SG_ID` | `sg-09896b73bb44d0ac3` |
| `AWS_ACCESS_KEY_ID` | Clé IAM |
| `AWS_SECRET_ACCESS_KEY` | Clé secrète IAM |
| `AWS_DEFAULT_REGION` | `eu-west-1` |

### Déploiement manuel (urgence)

```bash
# 1. Ajouter son IP au Security Group
MY_IP=$(curl -s https://checkip.amazonaws.com)
aws --region eu-west-1 ec2 authorize-security-group-ingress \
  --group-id sg-09896b73bb44d0ac3 \
  --ip-permissions "[{\"IpProtocol\":\"tcp\",\"FromPort\":22,\"ToPort\":22,\"IpRanges\":[{\"CidrIp\":\"${MY_IP}/32\"}]}]"

# 2. Pousser la clé et se connecter (fenêtre 60s)
aws --region eu-west-1 ec2-instance-connect send-ssh-public-key \
  --instance-id i-0fc0adfd256c0428d \
  --instance-os-user ec2-user \
  --ssh-public-key file://~/.ssh/petrix-ec2.pub && \
ssh -i ~/.ssh/petrix-ec2 ec2-user@3.255.126.244

# 3. Sur EC2 : rebuild
cd /home/ec2-user/petrix
docker compose -f docker/docker-compose.prod.yml build
docker compose -f docker/docker-compose.prod.yml up -d --remove-orphans
```

---

## API

Tous les endpoints sont préfixés par `/api/v1`. Auth JWT : `Authorization: Bearer <token>`.

| Module | Préfixe | Endpoints principaux |
|--------|---------|---------------------|
| Auth | `/auth` | `POST /login`, `POST /verify-otp`, `GET /me` |
| Users | `/users` | CRUD utilisateurs, rôles |
| Assets | `/assets` | CRUD actifs |
| Vulnérabilités | `/vulnerabilities` | CRUD, liaison actifs/scans |
| Scans | `/scans` | CRUD, lancement, résultats |
| Dashboard | `/dashboard` | Métriques globales |
| SMSI | `/smsi` | Projets, documents, génération |
| Clients | `/clients` | CRUD clients, conformité |
| Pentest | `/pentest` | Targets, sessions, findings, rapports |
| **Hardening** | `/hardening` | Targets, sessions, findings, modules |
| System | `/system` | Health, audit logs |

### API Hardening

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET` | `/hardening/modules` | Liste des 5 modules disponibles |
| `POST` | `/hardening/targets` | Créer une cible SSH |
| `GET` | `/hardening/targets` | Lister les cibles |
| `DELETE` | `/hardening/targets/{id}` | Supprimer une cible |
| `POST` | `/hardening/sessions` | Lancer un audit de durcissement |
| `GET` | `/hardening/sessions` | Lister les sessions |
| `GET` | `/hardening/sessions/{id}` | Détail d'une session (score, grade) |
| `GET` | `/hardening/sessions/{id}/findings` | Findings d'une session |

---

## RBAC — Rôles et permissions

| Rôle | Description |
|------|-------------|
| `VIEWER` | Lecture seule (assets, vulns, dashboard) |
| `ANALYST` | + Créer/modifier vulns, scans, pentests, audits |
| `AUDITOR` | + Conformité, exports, génération SMSI |
| `ADMIN` | Toutes les permissions (users, settings, système) |

---

## Structure du projet

```
petrix/
├── backend/
│   ├── app/
│   │   ├── api/v1/              # Endpoints REST (11 modules)
│   │   │   ├── router.py
│   │   │   ├── auth.py
│   │   │   ├── hardening.py
│   │   │   └── ...
│   │   ├── core/                # JWT, bcrypt, RBAC
│   │   ├── hardening/           # Moteur d'audit de durcissement
│   │   │   ├── engine.py        # Orchestration + scoring
│   │   │   ├── ssh_connector.py # Paramiko SSH
│   │   │   └── modules/linux/   # 5 modules d'audit
│   │   ├── infrastructure/database/
│   │   │   ├── models.py
│   │   │   ├── hardening_models.py
│   │   │   ├── pentest_models.py
│   │   │   └── smsi_models.py
│   │   ├── pentest/             # Module PentestAI
│   │   ├── application/smsi/    # Générateur SMSI
│   │   ├── workers/             # Celery tasks
│   │   │   ├── celery_app.py
│   │   │   ├── hardening_tasks.py
│   │   │   └── pentest_tasks.py
│   │   ├── config.py
│   │   └── main.py
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/client.ts        # Client Axios + hardeningApi
│   │   ├── pages/
│   │   │   ├── hardening/HardeningPage.tsx
│   │   │   ├── pentest/
│   │   │   └── ...
│   │   └── components/layout/Sidebar.tsx
│   ├── Dockerfile
│   └── package.json
├── docker/
│   ├── docker-compose.yml       # Dev local (8 services, hot reload)
│   ├── docker-compose.prod.yml  # Prod EC2 (5 services)
│   └── nginx.prod.conf          # Reverse proxy prod
├── docs/
│   ├── projet/                  # Cahier des charges, Gantt, gestion de projet
│   ├── CHANGELOG.md
│   ├── DEPLOYMENT.md
│   ├── INSTALLATION_WINDOWS.md
│   ├── RUNBOOK-SECRET.md        # Infra AWS, credentials (non versionné)
│   └── infrastructure-petrix.drawio
├── scripts/
│   └── install.sh
├── .gitlab-ci.yml               # CI/CD : lint → test → build → deploy
├── Makefile
├── .env.example
└── README.md
```

---

## Tests

```bash
# Backend — dans le container
docker compose --env-file .env -f docker/docker-compose.yml exec backend pytest tests/ -v

# Frontend — dans le container
docker compose --env-file .env -f docker/docker-compose.yml exec frontend npm test

# Tests backend en local (venv activé)
cd backend && pytest tests/ -v
```

---

## À faire — Code

### Priorité haute

- [ ] **Migrations Alembic** — La DB tourne avec `create_all()`. Créer une migration initiale (`alembic revision --autogenerate`) et remplacer le `create_all` dans `main.py` par `alembic upgrade head`.

- [ ] **Frontend prod : build statique** — `docker-compose.prod.yml` utilise encore `npm run dev -- --host`. Remplacer par un Dockerfile multi-stage qui sert `npm run build` avec nginx.

- [ ] **MinIO : init automatique des buckets** — Ajouter dans `lifespan()` de `main.py` la création du bucket `petrix` s'il n'existe pas (via `minio` SDK ou `boto3`).

- [ ] **Tests module Hardening** — Ajouter `backend/tests/test_hardening_engine.py` (mock SSH) et `test_hardening_api.py` (endpoints).

- [ ] **Auth flow : MFA token expiry** — Vérifier que le `mfa_token` Redis a bien un TTL et est supprimé après usage.

### Priorité moyenne

- [ ] **Hardening : auth par clé SSH** — Implémenter l'upload et l'utilisation d'une clé privée PEM dans `SSHConnector` (le champ `key_file` existe mais le frontend ne le propose pas encore).

- [ ] **Collection Postman** — Créer `docs/petrix.postman_collection.json` avec les variables `{{base_url}}`, `{{token}}` et les requêtes de tous les modules.

- [ ] **Variables d'env non documentées** — `GROQ_API_KEY` est dans `.env` mais le module Pentest n'est pas branché sur Groq. Câbler Groq comme provider alternatif à Ollama ou supprimer la variable.

- [ ] **Logs Celery** — Brancher un handler Loguru dans `celery_app.py` pour que les logs remontent correctement.

- [ ] **Seed data Hardening** — Ajouter dans `scripts/seed_test_data.py` des `HardeningTarget` et sessions fictives pour que la page Hardening ne soit pas vide au démarrage.

### Priorité basse

- [ ] **Rate limiting** — Ajouter `slowapi` sur `/auth/login` et `/auth/verify-otp` pour limiter le brute-force.

- [ ] **Révoquer les credentials IAM exposés** — Voir `docs/RUNBOOK-SECRET.md`. Les clés `admin-noella` ont été exposées dans un chat. Les remplacer et mettre à jour les variables GitLab CI/CD.

- [ ] **Monitoring** — Ajouter `/metrics` compatible Prometheus (`prometheus-fastapi-instrumentator`) pour brancher Grafana Cloud sur la prod.

---

## Variables d'environnement

| Variable | Description | Dev |
|----------|-------------|-----|
| `POSTGRES_USER` | Utilisateur PostgreSQL | `petrix` |
| `POSTGRES_PASSWORD` | Mot de passe PostgreSQL | — |
| `POSTGRES_DB` | Nom de la base | `petrix` |
| `DATABASE_URL` | URL complète (prod : RDS) | auto-construite dans compose |
| `REDIS_URL` | URL Redis | `redis://redis:6379/0` |
| `SECRET_KEY` | Clé JWT — générer avec `openssl rand -hex 32` | — |
| `JWT_ALGORITHM` | Algorithme JWT | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Durée token | `30` |
| `CORS_ORIGINS` | Origines CORS autorisées | `http://localhost:5173` |
| `DEBUG` | Mode debug | `true` |
| `ADMIN_PASSWORD` | Mot de passe admin initial | — |
| `MINIO_ROOT_USER` | Utilisateur MinIO | `minioadmin` |
| `MINIO_ROOT_PASSWORD` | Mot de passe MinIO | `minioadmin123` |
| `MINIO_ENDPOINT` | Endpoint MinIO | `minio:9000` |
| `SMTP_HOST` | Serveur SMTP | `mailpit` (dev) |
| `SMTP_PORT` | Port SMTP | `1025` (dev) |
| `SMTP_TLS` | TLS SMTP | `false` (dev) |
| `SMTP_FROM_EMAIL` | Expéditeur | `noreply@petrix.local` |
| `AWS_DEFAULT_REGION` | Région AWS | `eu-west-1` |
| `S3_BUCKET` | Nom du bucket S3 (prod) | — |
| `GROQ_API_KEY` | Clé API Groq (optionnel) | — |
| `OLLAMA_API_URL` | URL Ollama (optionnel) | — |
