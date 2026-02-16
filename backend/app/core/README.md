# Core — Sécurité et RBAC

Module central de sécurité de Petrix.

## Fichiers

| Fichier | Rôle |
|---------|------|
| `security.py` | Fonctions JWT et hachage de mots de passe |
| `permissions.py` | Système RBAC complet (rôles, permissions, mappings) |

## Sécurité (`security.py`)

- **Hachage** : bcrypt via `passlib`
- **JWT** : Algorithme HS256, expiration configurable (`ACCESS_TOKEN_EXPIRE_MINUTES`)
- **Fonctions** :
  - `verify_password(plain, hashed)` — Vérifie un mot de passe
  - `get_password_hash(password)` — Hache un mot de passe
  - `create_access_token(data, expires_delta)` — Génère un token JWT
  - `decode_token(token)` — Décode et valide un token JWT

## RBAC (`permissions.py`)

### 4 rôles hiérarchiques

| Rôle | Niveau | Description |
|------|--------|-------------|
| `VIEWER` | 1 | Lecture seule sur toutes les ressources |
| `ANALYST` | 2 | + Création/modification (vulns, scans, pentests) |
| `AUDITOR` | 3 | + Conformité, exports, génération SMSI |
| `ADMIN` | 4 | Toutes les permissions (gestion users, système) |

### Catégories de permissions

- **Assets** : `ASSETS_VIEW`, `ASSETS_CREATE`, `ASSETS_EDIT`, `ASSETS_DELETE`
- **Vulnérabilités** : `VULNS_VIEW`, `VULNS_CREATE`, `VULNS_EDIT`, `VULNS_DELETE`
- **Scans** : `SCANS_VIEW`, `SCANS_CREATE`, `SCANS_RUN`, `SCANS_DELETE`
- **Pentest** : `PENTEST_VIEW`, `PENTEST_CREATE`, `PENTEST_RUN`, `PENTEST_DELETE`
- **Conformité** : `COMPLIANCE_VIEW`, `COMPLIANCE_ASSESS`, `COMPLIANCE_EXPORT`
- **Users** : `USERS_VIEW`, `USERS_CREATE`, `USERS_EDIT`, `USERS_DELETE`
- **Système** : `SYSTEM_SETTINGS`, `SYSTEM_AUDIT_LOGS`, `SYSTEM_ADMIN`

### Utilisation

```python
from app.core.permissions import Permission, has_permission

# Dans un endpoint FastAPI
@router.get("/assets")
async def list_assets(user = Depends(require_permission(Permission.ASSETS_VIEW))):
    ...
```
