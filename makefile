.PHONY: build run stop remove clean install dev test lint format

# Build the container image
build:
	podman build -f Dockerfile-service -t routing-table-api:latest .

# Run the container
run:
	podman run -dp 8080:5000 \
		--name routing-api \
		-e PROC_NUM=4 \
		-v $(PWD)/routes.txt:/app/routes.txt:ro \
		routing-table-api:latest

# Stop the running container
stop:
	podman stop routing-api || true

# Remove the container
remove: stop
	podman rm routing-api || true

# Remove the image
clean: remove
	podman rmi -f routing-table-api:latest || true

# Install Python dependencies locally
install:
	pip install -e .

# Install development dependencies
dev:
	pip install -e ".[dev]"

# Run tests
test:
	pytest

# Lint code
lint:
	ruff check service/

# Format code
format:
	black service/
	ruff check --fix service/