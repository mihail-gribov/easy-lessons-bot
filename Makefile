.PHONY: install lint fmt test run docker-build docker-run clean

# Install dependencies
install:
	uv sync

# Lint code
lint:
	uv run ruff check .

# Format code
fmt:
	uv run ruff format .

# Run tests
test:
	uv run pytest -q

# Run the application locally
run:
	uv run python -m app.main

# Build Docker image
docker-build:
	docker build -t easy-lessons-bot:local .

# Run Docker container
docker-run:
	docker run --env-file .env easy-lessons-bot:local

# Clean up generated files
clean:
	rm -rf __pycache__ .pytest_cache .ruff_cache
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
