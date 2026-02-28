# ──────────────────────────────────────────────────────────────
# Aquafin – Makefile
# Common commands for development, testing, and deployment.
# ──────────────────────────────────────────────────────────────

.DEFAULT_GOAL := help

# ── Docker ────────────────────────────────────────────────────

.PHONY: up down restart logs ps

up: ## Start all services (dev mode with hot reload)
	docker compose up -d

up-build: ## Build and start all services
	docker compose up -d --build

down: ## Stop all services
	docker compose down

down-clean: ## Stop all services and remove volumes
	docker compose down -v

restart: ## Restart all services
	docker compose restart

logs: ## Tail logs from all services
	docker compose logs -f

logs-backend: ## Tail backend logs
	docker compose logs -f backend

logs-frontend: ## Tail frontend logs
	docker compose logs -f frontend

ps: ## Show running services
	docker compose ps

# ── Backend ───────────────────────────────────────────────────

.PHONY: backend-shell backend-test backend-lint backend-format

backend-shell: ## Open a shell in the backend container
	docker compose exec backend bash

backend-test: ## Run backend tests
	cd backend && python -m pytest -v --cov=app

backend-lint: ## Lint backend code with ruff
	cd backend && python -m ruff check .

backend-format: ## Format backend code with ruff
	cd backend && python -m ruff format .

backend-migrate: ## Run Alembic migrations
	cd backend && python -m alembic upgrade head

backend-migrate-create: ## Create a new Alembic migration (usage: make backend-migrate-create MSG="add users")
	cd backend && python -m alembic revision --autogenerate -m "$(MSG)"

# ── Frontend ──────────────────────────────────────────────────

.PHONY: frontend-shell frontend-dev frontend-build frontend-lint

frontend-shell: ## Open a shell in the frontend container
	docker compose exec frontend sh

frontend-dev: ## Start frontend in dev mode (local, outside Docker)
	cd frontend && npm run dev

frontend-build: ## Build frontend for production
	cd frontend && npm run build

frontend-lint: ## Lint frontend code
	cd frontend && npm run lint

frontend-type-check: ## TypeScript type check
	cd frontend && npm run type-check

# ── Database ──────────────────────────────────────────────────

.PHONY: db-shell db-reset

db-shell: ## Open psql shell
	docker compose exec db psql -U aquafin -d aquafin

db-reset: ## Reset database (drop + recreate)
	docker compose exec db psql -U aquafin -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
	$(MAKE) backend-migrate

# ── Quality ───────────────────────────────────────────────────

.PHONY: lint test

lint: backend-lint frontend-lint ## Lint all code

test: backend-test ## Run all tests

# ── Help ──────────────────────────────────────────────────────

.PHONY: help

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
