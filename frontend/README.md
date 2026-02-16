# Frontend — Petrix

Interface web React pour la Petrix. SPA avec routing, state management, et composants réutilisables.

## Stack

- **React 18** + TypeScript
- **Vite 5** — Build tool et HMR
- **TailwindCSS 3** — Styles utilitaires
- **TanStack Query 5** — Data fetching et cache
- **Zustand** — State management (auth store)
- **React Router DOM 6** — Routing SPA
- **React Hook Form + Zod** — Formulaires et validation
- **Recharts** — Graphiques
- **Tiptap** — Éditeur de texte riche (SMSI)
- **Axios** — Client HTTP
- **Lucide React** — Icônes

## Structure

```
frontend/src/
├── api/
│   └── client.ts              # Client Axios + helpers API par module
├── stores/
│   └── authStore.ts           # Store Zustand (auth, token, user)
├── pages/
│   ├── DashboardPage.tsx      # Tableau de bord principal
│   ├── auth/LoginPage.tsx     # Page de connexion
│   ├── assets/AssetsPage.tsx  # Gestion des actifs
│   ├── vulnerabilities/VulnerabilitiesPage.tsx
│   ├── scans/ScansPage.tsx
│   ├── smsi/SMSIPage.tsx      # Projets et documents SMSI
│   ├── clients/ClientsPage.tsx
│   ├── users/UsersPage.tsx
│   ├── settings/SettingsPage.tsx
│   └── pentest/
│       ├── PentestPage.tsx           # Liste sessions et targets
│       ├── PentestSessionDetail.tsx  # Détail session (findings, MITRE, IA)
│       └── types.ts                  # Types TypeScript du module
├── components/
│   ├── layout/                # Layout, Header, Sidebar
│   ├── clients/               # ClientForm, ClientDetail, AssessmentView, etc.
│   └── smsi/                  # ProjectWizard, DocumentEditor, etc.
├── utils/
│   └── markdownConverter.ts   # Conversion markdown ↔ HTML
├── App.tsx                    # Routes et layout principal
└── main.tsx                   # Point d'entrée React
```

## Routes

| Route | Page | Description |
|-------|------|-------------|
| `/` | DashboardPage | Tableau de bord avec métriques |
| `/login` | LoginPage | Authentification JWT |
| `/assets` | AssetsPage | Inventaire des actifs |
| `/vulnerabilities` | VulnerabilitiesPage | Gestion des vulnérabilités |
| `/scans` | ScansPage | Scans de sécurité |
| `/smsi` | SMSIPage | Documents SMSI ISO 27001 |
| `/clients` | ClientsPage | Gestion clients et conformité |
| `/users` | UsersPage | Administration des utilisateurs |
| `/settings` | SettingsPage | Paramètres de l'application |
| `/pentest` | PentestPage | Sessions et cibles pentest |
| `/pentest/session/:id` | PentestSessionDetail | Détail d'une session pentest |

## Démarrage

```bash
# Via Docker (recommandé)
docker compose up -d frontend

# Développement local
npm install
npm run dev        # Serveur de développement (http://localhost:5173)
npm run build      # Build production
npm run test       # Tests unitaires (Vitest)
npm run lint       # ESLint
```

## Client API (`api/client.ts`)

Client Axios centralisé avec intercepteurs pour le token JWT. Expose des helpers par module :

```typescript
import { pentestApi, assetsApi, authApi } from '@/api/client';

// Exemples
await authApi.login(email, password);
await pentestApi.listSessions();
await pentestApi.createTarget({ name: 'Server', host: '10.0.0.1', port: 22 });
```
