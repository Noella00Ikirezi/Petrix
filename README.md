# GRC Platform

Plateforme de Gouvernance, Risque et Conformité (GRC) unifiée.

## Quick Start

### Option 1: Docker Compose (Recommandé)

```bash
# Démarrer tous les services
docker-compose up -d

# Voir les logs
docker-compose logs -f
```

Services:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Option 2: Développement local

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # ou venv\Scripts\activate sur Windows
pip install -r requirements.txt

# Démarrer PostgreSQL et Redis (ou utiliser Docker)
docker-compose up -d db redis

# Lancer le backend
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## Credentials par défaut

- Email: `admin@grc-platform.local`
- Password: `admin123`

## Architecture

```
02-grc-platform/
├── backend/           # FastAPI + SQLAlchemy
│   ├── app/
│   │   ├── api/v1/    # REST endpoints
│   │   ├── core/      # Security, permissions
│   │   └── infrastructure/
│   │       └── database/  # Models, repositories
│   └── requirements.txt
├── frontend/          # React + TypeScript + Vite
│   ├── src/
│   │   ├── pages/     # Dashboard, Assets, Vulns, Scans
│   │   ├── components/
│   │   └── api/       # API client
│   └── package.json
└── docker-compose.yml
```

## Fonctionnalités MVP

- [x] Auth JWT + RBAC (4 rôles)
- [x] Gestion des Assets
- [x] Gestion des Vulnérabilités
- [x] Gestion des Scans
- [x] Dashboard avec métriques
- [ ] Module Compliance (v1.0)
- [ ] Module Fournisseurs (v1.0)
- [ ] Assistant IA (v1.0)

## Stack Technique

- **Backend:** FastAPI, SQLAlchemy 2.0, PostgreSQL, Redis
- **Frontend:** React 18, TypeScript, TailwindCSS, Vite
- **Auth:** JWT + bcrypt
- **Charts:** Recharts
