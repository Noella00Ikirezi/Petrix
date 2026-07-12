# Petrix — Plateforme d'audit cybersécurité

> Projet annuel ESGI 4SI4 · Binôme : Noëlla IKIREZI & Mathieu MISSAK · Tuteur : Christophe NEY

Petrix est une plateforme SaaS self-hosted d'audit de sécurité informatique.

## Fonctionnalités

- **Hardening (HCO)** — Audit ANSSI-BP-028 sur Linux, macOS, Windows (80+ contrôles) avec score A–F, CVE associées et rapport Mistral AI
- **Inventaire** — Gestion des actifs réseau (CRUD + scans nmap automatisés)
- **Vulnérabilités** — Suivi CVE avec flux CERT-FR en temps réel et corrélations automatiques
- **RBAC** — 4 rôles : VIEWER < ANALYST < AUDITOR < ADMIN
- **MFA** — Authentification 2FA par email OTP

## Stack

| Couche | Technologie |
|--------|-------------|
| Backend API | FastAPI 0.109 · Python 3.11 · Uvicorn |
| Base de données | PostgreSQL (AWS RDS) · SQLAlchemy 2.0 · Alembic |
| File d'attente | Celery 5.3 · Redis 7 |
| Frontend | React 18 · TypeScript 5.3 · Vite 5 · Tailwind CSS 3.4 |
| IA | Mistral AI (clé via AWS SSM SecureString) |
| Infrastructure | Docker Compose · AWS EC2 (t3.small, eu-west-1) · Nginx |

## Déploiement production

```
https://petrix.noellahome.org
```

## Lancer en local (dev)

```bash
cp .env.example .env      # configurer les variables
make dev                  # lance tous les containers Docker
```

## Structure

```
backend/
  app/
    api/v1/        # endpoints REST (auth, hardening, vulns, assets, feed…)
    core/          # sécurité JWT, RBAC, audit trail
    hardening/     # moteur HCO + agents shell (linux.sh, macos.sh, windows.ps1)
    infrastructure/database/  # modèles SQLAlchemy + connexion
    workers/       # tâches Celery (hardening, scan, email)
  alembic/versions/          # migrations de schéma
frontend/
  src/
    api/           # client Axios + endpoints
    pages/         # pages React (Dashboard, Hardening, Vulns…)
    stores/        # état global Zustand
    components/    # layout (Sidebar, Header)
    data/          # base de connaissances HCO
docker/            # docker-compose.prod.yml · nginx.prod.conf
```
