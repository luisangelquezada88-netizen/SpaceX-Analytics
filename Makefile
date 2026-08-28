.PHONY: help install test run-dashboard run-notebooks build up down clean lint

# Default target
help:
	@echo "SpaceX Falcon 9 Landing Prediction - Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  install       Install dependencies in virtual environment"
	@echo "  build         Build Docker image"
	@echo ""
	@echo "Run locally:"
	@echo "  run-dashboard Run Dash dashboard on http://localhost:8051"
	@echo "  run-notebooks Run Jupyter Lab on http://localhost:8888"
	@echo ""
	@echo "Docker:"
	@echo "  up            Start all services (dashboard + notebooks)"
	@echo "  up-dashboard  Start only dashboard"
	@echo "  down          Stop all services"
	@echo "  logs          View logs"
	@echo ""
	@echo "Quality:"
	@echo "  lint          Run linting (ruff/flake8)"
	@echo "  test          Run tests"
	@echo ""
	@echo "Cleanup:"
	@echo "  clean         Remove build artifacts and caches"

# Setup
install:
	python -m venv .venv && .venv/bin/pip install --upgrade pip && .venv/bin/pip install -r requirements.txt

build:
	docker compose build

# Local development
run-dashboard:
	.venv/bin/python app/spacex_dash_app.py

run-notebooks:
	.venv/bin/jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --NotebookApp.token=''

# Docker
up:
	docker compose up -d

up-dashboard:
	docker compose up -d spacex-dashboard

up-notebooks:
	docker compose --profile dev up -d spacex-notebooks

down:
	docker compose down

logs:
	docker compose logs -f

# Quality
lint:
	.venv/bin/ruff check . || .venv/bin/flake8 .

test:
	.venv/bin/pytest tests/ -v

# Cleanup
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .coverage htmlcov .pytest_cache .ruff_cache 2>/dev/null || true
	docker compose down -v 2>/dev/null || true