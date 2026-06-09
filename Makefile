# ══════════════════════════════════════════════
# NetWatch AI — Makefile
# ══════════════════════════════════════════════

COMPOSE = docker compose
PROFILE ?= standard

# Determine compose file based on profile
ifeq ($(PROFILE),minimal)
	COMPOSE_FILE = -f docker-compose.yml -f docker-compose.minimal.yml
else ifeq ($(PROFILE),full)
	COMPOSE_FILE = -f docker-compose.yml -f docker-compose.full.yml
else
	COMPOSE_FILE = -f docker-compose.yml
endif

.PHONY: help up down restart logs status build clean shell-backend shell-capture shell-ml test lint db-migrate db-upgrade

help: ## Show this help message
	@echo "NetWatch AI — Available Commands"
	@echo "════════════════════════════════════════"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ── Service Management ─────────────────────────

up: ## Start all services (PROFILE=minimal|standard|full)
	$(COMPOSE) $(COMPOSE_FILE) up -d
	@echo "\n✅ NetWatch is running"
	@echo "   Dashboard: http://localhost:3000"
	@echo "   API:       http://localhost:8000"
	@echo "   API Docs:  http://localhost:8000/docs"

down: ## Stop all services
	$(COMPOSE) $(COMPOSE_FILE) down
	@echo "⬇️  NetWatch stopped"

restart: ## Restart all services
	$(COMPOSE) $(COMPOSE_FILE) restart

logs: ## Show combined logs (follow)
	$(COMPOSE) $(COMPOSE_FILE) logs -f --tail=100

logs-backend: ## Show backend logs
	$(COMPOSE) $(COMPOSE_FILE) logs -f backend

logs-capture: ## Show capture agent logs
	$(COMPOSE) $(COMPOSE_FILE) logs -f capture-agent

logs-ml: ## Show ML engine logs
	$(COMPOSE) $(COMPOSE_FILE) logs -f ml-engine

status: ## Show service status
	$(COMPOSE) $(COMPOSE_FILE) ps

# ── Build ──────────────────────────────────────

build: ## Build all images
	$(COMPOSE) $(COMPOSE_FILE) build

build-backend: ## Build backend image only
	$(COMPOSE) $(COMPOSE_FILE) build backend

build-capture: ## Build capture agent image only
	$(COMPOSE) $(COMPOSE_FILE) build capture-agent

build-frontend: ## Build frontend image only
	$(COMPOSE) $(COMPOSE_FILE) build frontend

# ── Shell Access ───────────────────────────────

shell-backend: ## Shell into backend container
	$(COMPOSE) $(COMPOSE_FILE) exec backend /bin/bash

shell-capture: ## Shell into capture agent container
	$(COMPOSE) $(COMPOSE_FILE) exec capture-agent /bin/bash

shell-ml: ## Shell into ML engine container
	$(COMPOSE) $(COMPOSE_FILE) exec ml-engine /bin/bash

# ── Database ───────────────────────────────────

db-migrate: ## Create a new migration (MSG="description")
	$(COMPOSE) $(COMPOSE_FILE) exec backend alembic revision --autogenerate -m "$(MSG)"

db-upgrade: ## Run pending migrations
	$(COMPOSE) $(COMPOSE_FILE) exec backend alembic upgrade head

db-downgrade: ## Rollback one migration
	$(COMPOSE) $(COMPOSE_FILE) exec backend alembic downgrade -1

# ── Testing ────────────────────────────────────

test: ## Run all tests
	$(COMPOSE) $(COMPOSE_FILE) exec backend pytest -v
	$(COMPOSE) $(COMPOSE_FILE) exec capture-agent pytest -v

test-backend: ## Run backend tests only
	$(COMPOSE) $(COMPOSE_FILE) exec backend pytest -v

test-capture: ## Run capture agent tests only
	$(COMPOSE) $(COMPOSE_FILE) exec capture-agent pytest -v

# ── Linting ────────────────────────────────────

lint: ## Lint all Python code
	$(COMPOSE) $(COMPOSE_FILE) exec backend ruff check src/
	$(COMPOSE) $(COMPOSE_FILE) exec backend ruff format --check src/

lint-fix: ## Auto-fix lint issues
	$(COMPOSE) $(COMPOSE_FILE) exec backend ruff check --fix src/
	$(COMPOSE) $(COMPOSE_FILE) exec backend ruff format src/

# ── Cleanup ────────────────────────────────────

clean: ## Remove containers, volumes, and built images
	$(COMPOSE) $(COMPOSE_FILE) down -v --rmi local
	@echo "🧹 Cleaned up"

clean-data: ## Remove database and model files (DESTRUCTIVE)
	@echo "⚠️  This will delete all NetWatch data!"
	@read -p "Are you sure? [y/N] " confirm && [ "$$confirm" = "y" ] && rm -rf data/netwatch.db data/netwatch.db-wal data/ml-models/*.pkl || echo "Cancelled"

# ── Utility ────────────────────────────────────

env: ## Create .env from .env.example
	@if [ ! -f .env ]; then cp .env.example .env && echo "✅ Created .env — edit it before starting"; else echo "⚠️  .env already exists"; fi

health: ## Check health of all services
	@echo "Checking service health..."
	@curl -sf http://localhost:8000/health && echo "✅ Backend OK" || echo "❌ Backend DOWN"
	@curl -sf http://localhost:8001/health && echo "✅ ML Engine OK" || echo "❌ ML Engine DOWN"
	@curl -sf http://localhost:3000 && echo "✅ Frontend OK" || echo "❌ Frontend DOWN"
