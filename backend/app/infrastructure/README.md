# Infrastructure — Base de données

Couche d'accès aux données avec SQLAlchemy 2.0 et PostgreSQL 16.

## Structure

```
infrastructure/
└── database/
    ├── __init__.py                    # get_db(), engine, SessionLocal
    ├── models.py                      # Modèles core (User, Asset, Vuln, Scan)
    ├── pentest_models.py              # Modèles PentestAI
    ├── smsi_models.py                 # Modèles SMSI
    └── client_requirements_models.py  # Modèles clients/conformité
```

## Modèles principaux

### `models.py`

| Modèle | Table | Description |
|--------|-------|-------------|
| `User` | `users` | Utilisateur (email, password hash, rôle, statut) |
| `Asset` | `assets` | Actif informatique (nom, type, statut, criticité, IP, OS) |
| `Vulnerability` | `vulnerabilities` | Vulnérabilité (titre, sévérité, CVE, statut, lié à asset) |
| `Scan` | `scans` | Scan de sécurité (type, statut, résultats JSON) |
| `AuditLog` | `audit_logs` | Journal d'audit (action, user, timestamp) |

**Enums** : `AssetType` (9 types), `AssetStatus` (4 statuts), `Severity` (5 niveaux), `ScanType`, `ScanStatus`, `VulnStatus`.

### `pentest_models.py`

| Modèle | Table | Description |
|--------|-------|-------------|
| `PentestTarget` | `pentest_targets` | Cible SSH (host, port, credentials) |
| `AuditSession` | `audit_sessions` | Session de pentest (statut, progression, score) |
| `PentestFinding` | `pentest_findings` | Découverte (sévérité, MITRE, evidence, remédiation) |
| `MitreTechnique` | `mitre_techniques` | Technique MITRE ATT&CK |

**Enums** : `AuditSessionStatus` (9 états), `AuditModuleType` (5 modules), `FindingCategory`.

## Connexion

```python
from app.infrastructure.database import get_db

# Dépendance FastAPI
def my_endpoint(db: Session = Depends(get_db)):
    users = db.query(User).all()
```

Les tables sont créées automatiquement au démarrage via `Base.metadata.create_all()` dans `main.py`.
