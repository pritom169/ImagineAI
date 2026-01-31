.PHONY: help build up down restart logs logs-api logs-worker migrate migrate-create migrate-downgrade test test-cov test-ml lint lint-fix seed django-shell django-createsuperuser shell-api shell-worker clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

# Docker
build: ## Build all Docker images
	docker compose build

up: ## Start all services
	docker compose up -d

down: ## Stop all services
	docker compose down

restart: ## Restart all services
	docker compose restart

logs: ## Tail logs for all services
	docker compose logs -f

logs-api: ## Tail FastAPI logs
	docker compose logs -f fastapi

logs-worker: ## Tail Celery worker logs
	docker compose logs -f celery-worker

# Database
migrate: ## Run Alembic migrations
	docker compose exec fastapi alembic -c backend/alembic/alembic.ini upgrade head

migrate-create: ## Create a new migration
	docker compose exec fastapi alembic -c backend/alembic/alembic.ini revision --autogenerate -m "$(msg)"

migrate-downgrade: ## Downgrade one migration
	docker compose exec fastapi alembic -c backend/alembic/alembic.ini downgrade -1

# Testing
test: ## Run all backend tests
	docker compose exec fastapi python -m pytest backend/tests -v

test-cov: ## Run tests with coverage
	docker compose exec fastapi python -m pytest backend/tests --cov=backend --cov-report=html -v

test-ml: ## Run ML tests only
	docker compose exec fastapi python -m pytest backend/tests/test_ml -v

# Linting
lint: ## Run linters
	docker compose exec fastapi python -m ruff check backend/

lint-fix: ## Fix linting issues
	docker compose exec fastapi python -m ruff check backend/ --fix

# Seed Data
seed: ## Seed the database with demo data
	docker compose exec fastapi python scripts/seed_data.py

# Django Admin
django-shell: ## Open Django shell
	docker compose exec django-admin python django_app/manage.py shell

django-createsuperuser: ## Create Django superuser
	docker compose exec django-admin python django_app/manage.py createsuperuser

# Utilities
shell-api: ## Shell into FastAPI container
	docker compose exec fastapi bash

shell-worker: ## Shell into Celery worker container
	docker compose exec celery-worker bash

clean: ## Remove all containers, volumes, and images
	docker compose down -v --rmi local
