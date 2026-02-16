# Tests — Suite de tests backend

Tests unitaires Python avec Pytest.

## Fichiers

| Fichier | Description |
|---------|-------------|
| `conftest.py` | Fixtures partagées (client de test, session DB, utilisateur admin) |
| `test_config.py` | Tests de la configuration Pydantic Settings |
| `test_health.py` | Test de l'endpoint `/health` |
| `test_licensing.py` | Tests du système de licensing |
| `test_permissions.py` | Tests RBAC (rôles, permissions, hiérarchie) |
| `test_security.py` | Tests JWT (création, validation, expiration) et bcrypt |

## Lancer les tests

```bash
# Via Docker (recommandé)
docker compose exec backend pytest
docker compose exec backend pytest -v              # Verbose
docker compose exec backend pytest tests/test_security.py  # Un fichier

# Environnement de test isolé
make test-run

# En local (venv activé)
cd backend && pytest
```
