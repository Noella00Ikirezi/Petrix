# Backend — Petrix

API REST FastAPI pour la plateforme d'audit cybersécurité Petrix.

## Stack

| Composant | Technologie |
|-----------|-------------|
| Framework | FastAPI 0.109 · Uvicorn |
| Base de données | PostgreSQL (AWS RDS) · SQLAlchemy 2.0 · Alembic |
| File d'attente | Celery 5.3 · Redis 7 |
| Authentification | JWT (python-jose) · bcrypt · OTP email (MFA) |
| Réseau | nmap · Scapy · paramiko (SSH) |
| IA | Mistral AI (clé via AWS SSM SecureString) |

## Structure

```
backend/
├── app/
│   ├── main.py                    # Point d'entrée FastAPI — lifespan, CORS, routes
│   ├── config.py                  # Variables d'environnement (Pydantic Settings)
│   ├── api/v1/
│   │   ├── router.py              # Assemblage des routes
│   │   ├── auth.py                # Connexion, OTP, tokens JWT
│   │   ├── hardening.py           # Audit HCO (lancement, résultats, rapport IA)
│   │   ├── assets.py              # Inventaire des actifs réseau
│   │   ├── vulnerabilities.py     # CVE — CRUD et corrélations
│   │   ├── feed.py                # Flux CERT-FR en temps réel
│   │   ├── dashboard.py           # Statistiques globales
│   │   ├── users.py               # Gestion des utilisateurs (admin)
│   │   ├── audit_logs.py          # Journal d'audit (RBAC)
│   │   ├── scans.py               # Scans réseau (Celery)
│   │   ├── agent_download.py      # Téléchargement de l'agent terrain
│   │   ├── system.py              # Santé système + licence
│   │   └── deps.py                # Dépendances FastAPI (auth, RBAC)
│   ├── core/
│   │   ├── security.py            # JWT, bcrypt, OTP
│   │   ├── permissions.py         # RBAC — VIEWER < ANALYST < AUDITOR < ADMIN
│   │   ├── audit.py               # Traçabilité des actions
│   │   ├── redis.py               # Blacklist tokens, rate limiting, OTP TTL
│   │   ├── email.py               # Envoi SMTP (invitation, OTP)
│   │   └── licensing.py           # Gestion de licence
│   ├── hardening/
│   │   ├── engine.py              # Moteur HCO — orchestration des audits
│   │   ├── cve_mapping.py         # Corrélation contrôles ANSSI ↔ CVE
│   │   ├── ssh_connector.py       # Connexion SSH distante (paramiko)
│   │   ├── agents/                # Scripts terrain : linux.sh, macos.sh, windows.ps1
│   │   └── modules/
│   │       ├── linux/             # 10 modules audit + remédiation (ANSSI-BP-028)
│   │       └── macos/             # 10 modules Intel + Silicon
│   ├── infrastructure/database/
│   │   ├── connection.py          # Moteur SQLAlchemy + factory de sessions
│   │   ├── models.py              # ORM : User, Asset, Scan, Vulnerability, AuditLog
│   │   └── hardening_models.py    # ORM : HardeningSession, HardeningFinding
│   ├── pentest/scanners/
│   │   └── vuln_scanner.py        # Détection CVE via nmap NSE + API CIRCL
│   ├── scanners/
│   │   ├── network_discovery.py   # Découverte réseau (nmap/Scapy)
│   │   └── rich_scan.py           # Scan approfondi (ports, OS, services)
│   └── workers/
│       ├── celery_app.py          # Configuration Celery + Redis broker
│       ├── hardening_tasks.py     # Tâche async audit HCO
│       ├── scan_tasks.py          # Tâche async scan réseau
│       └── email_tasks.py         # Tâche async envoi email
├── alembic/versions/              # Migrations de schéma (001 initial, 005 scan-asset)
├── Dockerfile                     # Image de production
└── requirements.txt               # Dépendances Python

```

## Démarrage

```bash
# Production (Docker)
docker compose -f docker/docker-compose.prod.yml --env-file .env.dev up -d

# Développement local
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Swagger UI

`https://petrix.noellahome.org/api/docs` — disponible en production.
