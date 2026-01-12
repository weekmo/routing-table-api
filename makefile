.PHONY: build run runv remove removeimg devrun test test-cov coverage-report lint format type-check clean help

# Default target
help:
	@echo "Available targets:"
	@echo "  make build        - Build Podman image"
	@echo "  make run          - Run container (production mode)"
	@echo "  make runv         - Run container with volume mount"
	@echo "  make remove       - Stop and remove container"
	@echo "  make removeimg    - Remove Podman image"
	@echo "  make devrun       - Run service locally with auto-reload"
	@echo "  make test         - Run all tests with verbose output"
	@echo "  make test-cov     - Run tests with coverage report"
	@echo "  make coverage-report - Open HTML coverage report in browser"
	@echo "  make lint         - Run ruff linter"
	@echo "  make format       - Format code with ruff"
	@echo "  make type-check   - Run mypy type checker"
	@echo "  make clean        - Clean Python cache files"
	@echo "  make install      - Install package in editable mode with dev dependencies"
	@echo "  make compose-up   - Start services with podman-compose"
	@echo "  make compose-down - Stop services with podman-compose"
	@echo "  make build-runtime- Build production Podman image"
	@echo "  make build-dev    - Build development Podman image with tests"
	@echo "  make build-all    - Build all Podman image stages"
	@echo "  make image-size   - Display Podman image sizes"
	@echo "  make pod-up       - Start pod with podman play kube"
	@echo "  make pod-down     - Stop pod"
	@echo "  make pod-logs     - View pod logs"

# Podman targets
build:
	podman build -t routing-table-api:latest .

compose-up:
	podman-compose up -d

compose-down:
	podman-compose down
	
runv:
	podman run -d -p 5000:5000 --name routing-api -v $(PWD)/routes.txt:/app/routes.txt:ro,Z routing-table-api:latest

run:
	podman run -d -p 5000:5000 --name routing-api routing-table-api:latest

remove:
	podman stop routing-api || true
	podman rm routing-api || true

removeimg:
	podman rmi -f routing-table-api:latest

# Development targets
install:
	pip install -e ".[dev]"

devrun:
	uvicorn service.main:app --reload --host 0.0.0.0 --port 5000

test:
	pytest tests/ -v --tb=short

test-cov:
	pytest tests/test_lpm.py tests/test_concurrency.py --cov=service --cov-report=term-missing --cov-report=html --cov-report=xml -v

coverage-report:
	@if [ -f htmlcov/index.html ]; then \
		echo "Opening coverage report in browser..."; \
		xdg-open htmlcov/index.html 2>/dev/null || open htmlcov/index.html 2>/dev/null || echo "Please open htmlcov/index.html manually"; \
	else \
		echo "No coverage report found. Run 'make test-cov' first."; \
	fi

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
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -exec rm -f {} + 2>/dev/null || true
	find . -type f -name ".coverage.*" -exec rm -f {} + 2>/dev/null || true
	find . -type f -name "coverage.xml" -exec rm -f {} + 2>/dev/null || true
	find . -type f -name "coverage-badge.svg" -exec rm -f {} + 2>/dev/null || true
	find . -type f -name "*.cover" -exec rm -f {} + 2>/dev/null || true

# Multi-stage Podman build targets
build-runtime:
	podman build --target runtime -t routing-table-api:latest .

build-dev:
	podman build --target development -t routing-table-api:test .

build-all:
	podman build --target builder -t routing-table-api:builder .
	podman build --target runtime -t routing-table-api:latest .
	podman build --target development -t routing-table-api:test .

image-size:
	@echo "Podman image sizes:"
	@podman images routing-table-api --format "table {{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"

# Podman-specific deployment targets
pod-up:
	podman play kube podman-pod.yaml

pod-down:
	podman play kube --down podman-pod.yaml

pod-logs:
	podman logs -f routing-table-api-pod-api
