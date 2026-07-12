# Frontend — Petrix

Interface web React pour la plateforme d'audit cybersécurité Petrix.

## Stack

| Bibliothèque | Rôle |
|---|---|
| React 18 + TypeScript 5 | Framework UI |
| Vite 5 | Build tool + HMR |
| Tailwind CSS 3 | Design system (tokens CSS custom) |
| Zustand | State global (authentification) |
| React Router DOM 6 | Routing SPA |
| Axios | Client HTTP + intercepteurs JWT |
| TanStack Query 5 | Cache et data fetching async |
| React Hook Form + Zod | Formulaires et validation |
| Recharts | Graphiques (dashboard, scores) |
| Lucide React | Icônes |
| react-hot-toast | Notifications |

## Structure

```
frontend/src/
├── api/
│   └── client.ts                          # Client Axios + groupes d'API par module
├── stores/
│   └── authStore.ts                       # Store Zustand (user, token, logout)
├── components/layout/
│   ├── Layout.tsx                         # Shell de l'application (sidebar + header)
│   ├── Header.tsx                         # Barre top (dark mode, notifs, menu profil)
│   └── Sidebar.tsx                        # Navigation principale (RBAC)
├── pages/
│   ├── HomePage.tsx                       # Landing page publique (3D + hero)
│   ├── DashboardPage.tsx                  # Tableau de bord (score global, métriques)
│   ├── hardening/HardeningPage.tsx        # Audit HCO (lancement, fiches, rapport IA)
│   ├── assets/AssetsPage.tsx              # Inventaire actifs + agent de déploiement
│   ├── vulnerabilities/VulnerabilitiesPage.tsx  # CVE + flux CERT-FR + corrélations
│   ├── audit-report/AuditReportPage.tsx   # Rapport d'audit imprimable (PDF)
│   ├── audit/AuditLogsPage.tsx            # Journal d'audit (AUDITOR+)
│   ├── users/UsersPage.tsx                # Gestion utilisateurs (ADMIN)
│   ├── settings/SettingsPage.tsx          # Profil, avatar, sécurité, thème
│   ├── support/SupportPage.tsx            # FAQ + formulaire de support
│   └── auth/
│       ├── LoginPage.tsx                  # Connexion + OTP MFA
│       ├── SigninPage.tsx                 # Inscription
│       └── ChangePasswordPage.tsx         # Changement de mot de passe obligatoire
├── data/
│   └── moduleKnowledge.ts                # Base de connaissances HCO (80+ contrôles)
├── App.tsx                               # Routes + guards RBAC (ProtectedRoute)
├── main.tsx                              # Point d'entrée React + QueryClient
└── index.css                            # Design tokens CSS (--bg, --panel, --lime…)
```

## Routes

| Route | Accès minimum | Description |
|---|---|---|
| `/` | Public | Landing page |
| `/login` | Public | Connexion MFA |
| `/dashboard` | VIEWER | Tableau de bord |
| `/hardening` | VIEWER | Audit HCO |
| `/assets` | VIEWER | Actifs réseau |
| `/vulnerabilities` | VIEWER | CVE + CERT-FR |
| `/audit` | VIEWER | Rapport d'audit |
| `/audit-logs` | AUDITOR | Journal d'audit |
| `/users` | ADMIN | Gestion utilisateurs |
| `/settings` | VIEWER | Paramètres |
| `/support` | VIEWER | Support |

## Démarrage

```bash
npm install
npm run dev      # http://localhost:5173
npm run build    # Build production
```
