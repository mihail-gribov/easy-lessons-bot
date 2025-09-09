.PHONY: install lint fmt test run docker-build docker-run clean kill-bots

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
