# GRC Platform - Makefile
# ========================
# Commandes pratiques pour gérer les environnements

.PHONY: help dev test prod clean seed logs shell

# Couleurs
CYAN := \033[36m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
RESET := \033[0m

help: ## Affiche cette aide
	@echo ""
	@echo "$(CYAN)GRC Platform - Commandes disponibles$(RESET)"
	@echo "======================================"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(RESET) %s\n", $$1, $$2}'
	@echo ""

# ====================
# ENVIRONNEMENT DEV
# ====================

dev: ## Lance l'environnement de développement
	@echo "$(CYAN)🚀 Démarrage environnement DEV...$(RESET)"
	docker-compose up -d
	@echo "$(GREEN)✓ Services démarrés$(RESET)"
	@echo ""
	@echo "  Frontend: http://localhost:5173"
	@echo "  Backend:  http://localhost:8000"
	@echo "  API Docs: http://localhost:8000/docs"
	@echo ""

dev-build: ## Rebuild et lance l'environnement de développement
	@echo "$(CYAN)🔨 Build et démarrage environnement DEV...$(RESET)"
	docker-compose up -d --build

dev-down: ## Arrête l'environnement de développement
	@echo "$(YELLOW)⏹ Arrêt environnement DEV...$(RESET)"
	docker-compose down

dev-logs: ## Affiche les logs de dev (follow)
	docker-compose logs -f

dev-logs-backend: ## Affiche les logs du backend de dev
	docker-compose logs -f backend

# ====================
# ENVIRONNEMENT TEST
# ====================

test: ## Lance l'environnement de test isolé
	@echo "$(CYAN)🧪 Démarrage environnement TEST...$(RESET)"
	docker-compose -f docker-compose.test.yml up -d
	@echo "$(GREEN)✓ Services de test démarrés$(RESET)"
	@echo ""
	@echo "  Frontend: http://localhost:5174"
	@echo "  Backend:  http://localhost:8001"
	@echo "  API Docs: http://localhost:8001/docs"
	@echo ""
	@echo "  DB Port:    5433"
	@echo "  Redis Port: 6380"
	@echo ""

test-build: ## Rebuild et lance l'environnement de test
	@echo "$(CYAN)🔨 Build et démarrage environnement TEST...$(RESET)"
	docker-compose -f docker-compose.test.yml up -d --build

test-down: ## Arrête l'environnement de test
	@echo "$(YELLOW)⏹ Arrêt environnement TEST...$(RESET)"
	docker-compose -f docker-compose.test.yml down

test-clean: ## Arrête et supprime les données de test
	@echo "$(RED)🗑 Nettoyage complet environnement TEST...$(RESET)"
	docker-compose -f docker-compose.test.yml down -v --remove-orphans

test-logs: ## Affiche les logs de test (follow)
	docker-compose -f docker-compose.test.yml logs -f

test-run: ## Exécute les tests unitaires
	@echo "$(CYAN)🧪 Exécution des tests...$(RESET)"
	docker-compose -f docker-compose.test.yml --profile test up test-runner --abort-on-container-exit

# ====================
# SEED DATA
# ====================

seed: ## Peuple la DB de dev avec des données de test
	@echo "$(CYAN)🌱 Seeding DB de développement...$(RESET)"
	docker-compose exec backend python -m scripts.seed_test_data

seed-test: ## Peuple la DB de test avec des données de test
	@echo "$(CYAN)🌱 Seeding DB de test...$(RESET)"
	docker-compose -f docker-compose.test.yml --profile seed up seed-data --abort-on-container-exit

seed-local: ## Seed en local (sans Docker) - nécessite venv activé
	@echo "$(CYAN)🌱 Seeding DB locale...$(RESET)"
	cd backend && python -m scripts.seed_test_data

# ====================
# UTILITAIRES
# ====================

shell-backend: ## Ouvre un shell dans le container backend (dev)
	docker-compose exec backend bash

shell-backend-test: ## Ouvre un shell dans le container backend (test)
	docker-compose -f docker-compose.test.yml exec backend-test bash

shell-db: ## Ouvre psql dans le container DB (dev)
	docker-compose exec db psql -U grc -d grc_platform

shell-db-test: ## Ouvre psql dans le container DB (test)
	docker-compose -f docker-compose.test.yml exec db-test psql -U grc_test -d grc_platform_test

# ====================
# NETTOYAGE
# ====================

clean: ## Arrête tous les environnements
	@echo "$(YELLOW)⏹ Arrêt de tous les environnements...$(RESET)"
	-docker-compose down
	-docker-compose -f docker-compose.test.yml down
	@echo "$(GREEN)✓ Tous les services arrêtés$(RESET)"

clean-all: ## Supprime tous les containers, volumes et images du projet
	@echo "$(RED)🗑 Nettoyage complet...$(RESET)"
	-docker-compose down -v --remove-orphans --rmi local
	-docker-compose -f docker-compose.test.yml down -v --remove-orphans --rmi local
	@echo "$(GREEN)✓ Nettoyage terminé$(RESET)"

# ====================
# STATUS
# ====================

status: ## Affiche le status des containers
	@echo "$(CYAN)📊 Status des environnements$(RESET)"
	@echo ""
	@echo "=== DEV ==="
	@docker-compose ps 2>/dev/null || echo "Aucun service actif"
	@echo ""
	@echo "=== TEST ==="
	@docker-compose -f docker-compose.test.yml ps 2>/dev/null || echo "Aucun service actif"

# ====================
# RACCOURCIS
# ====================

up: dev ## Alias pour 'dev'
down: dev-down ## Alias pour 'dev-down'
logs: dev-logs ## Alias pour 'dev-logs'
ps: status ## Alias pour 'status'
