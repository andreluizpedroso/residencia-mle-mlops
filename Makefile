.PHONY: up down logs test lint format check install

COMPOSE_FILE := docker/docker-compose.yml
ENV_FILE     := .env

# ── Infraestrutura ──────────────────────────────────────────────────────────

up: ## Sobe a stack local (MLflow + PostgreSQL + MinIO)
	docker compose -f $(COMPOSE_FILE) --env-file $(ENV_FILE) up -d
	@echo ""
	@echo "  MLflow UI  → http://localhost:5000"
	@echo "  MinIO UI   → http://localhost:9001"
	@echo ""

down: ## Para e remove os containers (dados persistem nos volumes)
	docker compose -f $(COMPOSE_FILE) down

down-v: ## Para, remove containers E volumes (apaga todos os dados)
	docker compose -f $(COMPOSE_FILE) down -v

logs: ## Acompanha os logs em tempo real
	docker compose -f $(COMPOSE_FILE) logs -f

ps: ## Lista o status dos containers
	docker compose -f $(COMPOSE_FILE) ps

# ── Qualidade de Código ──────────────────────────────────────────────────────

lint: ## Executa ruff check (linting)
	uv run ruff check .

format: ## Formata o código com ruff format
	uv run ruff format .

check: lint ## Lint + type check (mypy)
	uv run mypy app pipelines

# ── Testes ───────────────────────────────────────────────────────────────────

test: ## Roda todos os testes
	uv run pytest

test-cov: ## Roda testes com relatório de cobertura
	uv run pytest --cov --cov-report=term-missing

# ── Setup ────────────────────────────────────────────────────────────────────

install: ## Instala dependências de desenvolvimento
	uv sync --extra dev

env: ## Cria .env a partir do template (não sobrescreve se já existir)
	@test -f .env || (cp .env.example .env && echo ".env criado — revise as credenciais")

help: ## Lista todos os comandos disponíveis
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'
