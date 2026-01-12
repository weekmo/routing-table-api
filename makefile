.PHONY: build run runv remove removeimg devrun test lint format type-check clean help

# Default target
help:
	@echo "Available targets:"
	@echo "  make build        - Build Docker image"
	@echo "  make run          - Run container (production mode)"
	@echo "  make runv         - Run container with volume mount"
	@echo "  make remove       - Stop and remove container"
	@echo "  make removeimg    - Remove Docker image"
	@echo "  make devrun       - Run service locally with auto-reload"
	@echo "  make test         - Run all tests with verbose output"
	@echo "  make lint         - Run ruff linter"
	@echo "  make format       - Format code with ruff"
	@echo "  make type-check   - Run mypy type checker"
	@echo "  make clean        - Clean Python cache files"
	@echo "  make install      - Install package in editable mode with dev dependencies"
	@echo "  make compose-up   - Start services with docker-compose"
	@echo "  make compose-down - Stop services with docker-compose"

# Docker targets (updated to use docker-compose instead of podman)
build:
	docker build -f Dockerfile-service -t routing-table-api:latest .

compose-up:
	docker-compose up -d

compose-down:
	docker-compose down
	
runv:
	docker run -dp 5000:5000 --name routing-api -v $(PWD)/routes.txt:/testwork/routes.txt routing-table-api:latest

run:
	docker run -dp 5000:5000 --name routing-api routing-table-api:latest

remove:
	docker stop routing-api || true
	docker rm routing-api || true

removeimg:
	docker rmi -f routing-table-api:latest

# Development targets
install:
	pip install -e ".[dev]"

devrun:
	uvicorn service.main:app --reload --host 0.0.0.0 --port 5000

test:
	pytest tests/ -v --tb=short

lint:
	ruff check service/ tests/

format:
	ruff format service/ tests/
	ruff check --fix service/ tests/

type-check:
	mypy service/ --ignore-missing-imports

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
