.PHONY: install lint fmt test run docker-build docker-build-tag docker-run docker-compose-up docker-compose-down docker-compose-dev docker-compose-logs docker-compose-restart docker-stop docker-logs docker-clean clean kill-bots help

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

# Build Docker image with custom tag
docker-build-tag:
	@read -p "Enter tag (default: latest): " tag; \
	tag=$${tag:-latest}; \
	docker build -t easy-lessons-bot:$$tag .

# Run Docker container
docker-run:
	docker run --env-file .env easy-lessons-bot:local

# Docker Compose commands
docker-compose-up:
	docker-compose up -d

docker-compose-down:
	docker-compose down

docker-compose-dev:
	docker-compose --profile dev up -d

docker-compose-logs:
	docker-compose logs -f

docker-compose-restart:
	docker-compose restart

# Docker container management
docker-stop:
	docker stop easy-lessons-bot 2>/dev/null || true
	docker rm easy-lessons-bot 2>/dev/null || true

docker-logs:
	docker logs -f easy-lessons-bot

docker-clean:
	docker system prune -f
	docker image prune -f

# Kill all running bot instances
kill-bots:
	@echo "🔍 Searching for running bot processes..."
	@if pgrep -f "python.*app\.main" > /dev/null; then \
		echo "💀 Killing bot processes..."; \
		pkill -f "python.*app\.main"; \
		sleep 1; \
		if pgrep -f "python.*app\.main" > /dev/null; then \
			echo "⚠️  Some processes still running, trying force kill..."; \
			pkill -9 -f "python.*app\.main"; \
		fi; \
		echo "✅ Bot processes terminated"; \
	else \
		echo "ℹ️  No bot processes found running"; \
	fi
	@echo "🔍 Checking for any remaining processes..."
	@if pgrep -f "python.*app\.main" > /dev/null; then \
		echo "❌ Some processes still running:"; \
		pgrep -f "python.*app\.main" | xargs ps -p; \
	else \
		echo "✅ All bot processes successfully terminated"; \
	fi

# Clean up generated files
clean:
	rm -rf __pycache__ .pytest_cache .ruff_cache
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Help command
help:
	@echo "Available commands:"
	@echo "  Development:"
	@echo "    install          - Install dependencies with uv"
	@echo "    run              - Run the bot locally"
	@echo "    lint             - Run code linting"
	@echo "    fmt              - Format code"
	@echo "    test             - Run tests"
	@echo ""
	@echo "  Docker (single container):"
	@echo "    docker-build     - Build Docker image"
	@echo "    docker-build-tag - Build Docker image with custom tag"
	@echo "    docker-run       - Run Docker container"
	@echo "    docker-stop      - Stop and remove Docker container"
	@echo "    docker-logs      - Show Docker container logs"
	@echo "    docker-clean     - Clean up Docker system"
	@echo ""
	@echo "  Docker Compose:"
	@echo "    docker-compose-up     - Start services in production mode"
	@echo "    docker-compose-dev    - Start services in development mode"
	@echo "    docker-compose-down   - Stop all services"
	@echo "    docker-compose-logs   - Show logs from all services"
	@echo "    docker-compose-restart- Restart all services"
	@echo ""
	@echo "  Utilities:"
	@echo "    kill-bots        - Kill all running bot processes"
	@echo "    clean            - Clean up generated files"
	@echo "    help             - Show this help message"
