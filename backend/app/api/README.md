# API v1 — Endpoints REST

Tous les endpoints sont montés sous `/api/v1` via `router.py`. Authentification JWT requise (sauf `/auth/login` et `/auth/register`).

## Modules

| Fichier | Préfixe | Description |
|---------|---------|-------------|
| `auth.py` | `/auth` | Login, register, profil courant |
| `users.py` | `/users` | CRUD utilisateurs, gestion des rôles |
| `assets.py` | `/assets` | CRUD actifs informatiques |
| `vulnerabilities.py` | `/vulnerabilities` | CRUD vulnérabilités |
| `scans.py` | `/scans` | CRUD scans de sécurité |
| `dashboard.py` | `/dashboard` | Métriques et statistiques globales |
| `system.py` | `/system` | Info système, health, audit logs |
| `smsi.py` | `/smsi` | Projets et documents SMSI |
| `clients.py` | `/clients` | Clients, exigences, conformité |
| `pentest.py` | `/pentest` | Targets, sessions, findings, IA |

## Fichiers communs

| Fichier | Rôle |
|---------|------|
| `router.py` | Routeur principal — monte tous les sous-routeurs |
| `deps.py` | Dépendances FastAPI : `get_current_user`, `require_permission`, `get_db` |

## Authentification

```
POST /api/v1/auth/login
Content-Type: application/x-www-form-urlencoded
Body: username=admin@petrix.local&password=admin123

→ { "access_token": "...", "token_type": "bearer" }
```

Puis inclure `Authorization: Bearer <token>` dans toutes les requêtes.

## Permissions

Chaque endpoint utilise `require_permission(Permission.XXX)` comme dépendance FastAPI. Les permissions sont vérifiées via le rôle de l'utilisateur courant. Voir `core/permissions.py` pour la liste complète.
