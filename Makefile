# Petrix - Makefile
# ========================
# Commandes pratiques pour gérer les environnements

.PHONY: help dev dev-build dev-down dev-logs dev-logs-backend \
        test test-build test-down test-clean test-logs test-run \
        seed seed-test seed-local \
        shell-backend shell-db \
        clean clean-all status up down logs ps

DC      := docker compose --env-file .env -f docker/docker-compose.yml
DC_TEST := docker compose --env-file .env -f docker/docker-compose.test.yml

# Couleurs
CYAN := \033[36m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
RESET := \033[0m

help: ## Affiche cette aide
	@echo ""
	@echo "$(CYAN)Petrix - Commandes disponibles$(RESET)"
	@echo "======================================"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-22s$(RESET) %s\n", $$1, $$2}'
	@echo ""

# ====================
# ENVIRONNEMENT DEV
# ====================

dev: ## Lance l'environnement de développement (hot reload)
	@echo "$(CYAN)Démarrage environnement DEV...$(RESET)"
	$(DC) up -d
	@echo "$(GREEN)Services démarrés$(RESET)"
	@echo ""
	@echo "  Frontend : http://localhost:5173"
	@echo "  Backend  : http://localhost:8000"
	@echo "  API Docs : http://localhost:8000/docs"
	@echo "  Adminer  : http://localhost:8080  (user: petrix / pw: grc_dev_2024)"
	@echo "  Mailpit  : http://localhost:8025  (emails OTP)"
	@echo "  MinIO    : http://localhost:9001  (minioadmin / minioadmin123)"
	@echo ""

dev-build: ## Rebuild les images et lance l'environnement de développement
	@echo "$(CYAN)Build + démarrage DEV...$(RESET)"
	$(DC) up -d --build

dev-down: ## Arrête l'environnement de développement
	@echo "$(YELLOW)Arrêt environnement DEV...$(RESET)"
	$(DC) down

dev-logs: ## Affiche les logs de dev (follow)
	$(DC) logs -f

dev-logs-backend: ## Affiche les logs du backend
	$(DC) logs -f backend

dev-logs-celery: ## Affiche les logs du worker Celery
	$(DC) logs -f celery

# ====================
# ENVIRONNEMENT TEST
# ====================

test: ## Lance l'environnement de test isolé
	@echo "$(CYAN)Démarrage environnement TEST...$(RESET)"
	$(DC_TEST) up -d
	@echo "$(GREEN)Services de test démarrés$(RESET)"

test-build: ## Rebuild et lance l'environnement de test
	$(DC_TEST) up -d --build

test-down: ## Arrête l'environnement de test
	$(DC_TEST) down

test-clean: ## Arrête et supprime les données de test
	@echo "$(RED)Nettoyage complet environnement TEST...$(RESET)"
	$(DC_TEST) down -v --remove-orphans

test-logs: ## Affiche les logs de test (follow)
	$(DC_TEST) logs -f

test-run: ## Exécute les tests unitaires dans le container
	$(DC_TEST) --profile test up test-runner --abort-on-container-exit

# ====================
# SEED DATA
# ====================

seed: ## Peuple la DB de dev avec des données de test
	@echo "$(CYAN)Seeding DB de développement...$(RESET)"
	$(DC) exec backend python -m scripts.seed_test_data

# ====================
# UTILITAIRES
# ====================

shell-backend: ## Ouvre un shell dans le container backend
	$(DC) exec backend bash

shell-db: ## Ouvre psql dans le container DB
	$(DC) exec db psql -U petrix -d petrix

# ====================
# NETTOYAGE
# ====================

clean: ## Arrête tous les environnements
	@echo "$(YELLOW)Arrêt de tous les environnements...$(RESET)"
	-$(DC) down
	-$(DC_TEST) down
	@echo "$(GREEN)Tous les services arrêtés$(RESET)"

clean-all: ## Supprime containers, volumes et images du projet
	@echo "$(RED)Nettoyage complet...$(RESET)"
	-$(DC) down -v --remove-orphans --rmi local
	-$(DC_TEST) down -v --remove-orphans --rmi local
	@echo "$(GREEN)Nettoyage terminé$(RESET)"

# ====================
# STATUS
# ====================

status: ## Affiche le status des containers
	@echo "$(CYAN)Status DEV$(RESET)"
	@$(DC) ps 2>/dev/null || echo "Aucun service actif"

# ====================
# RACCOURCIS
# ====================

up:   dev       ## Alias → dev
down: dev-down  ## Alias → dev-down
logs: dev-logs  ## Alias → dev-logs
ps:   status    ## Alias → status
build: dev-build ## Alias → dev-build
