# Scripts — Seed et utilitaires

Scripts de peuplement de la base de données et utilitaires de maintenance.

## Fichiers

| Script | Taille | Description |
|--------|--------|-------------|
| `seed_test_data.py` | ~14 Ko | Peuple la DB avec des données de test (assets, vulns, scans, users) |
| `seed_smsi_data.py` | ~30 Ko | Injecte les templates SMSI ISO 27001 complets |
| `add_directive_enum.py` | ~2 Ko | Ajoute un type d'enum directive à la DB |

## Utilisation

```bash
# Via Make (recommandé)
make seed                    # Seed DB de développement
make seed-test               # Seed DB de test

# Via Docker
docker compose exec backend python -m scripts.seed_test_data
docker compose exec backend python -m scripts.seed_smsi_data

# En local (venv activé)
cd backend && python -m scripts.seed_test_data
```
