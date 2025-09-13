# Easy Lessons Bot

A Telegram bot for simple, friendly explanations powered by an LLM (OpenRouter via OpenAI SDK).

## Features
- **Aiogram 3** (long polling)
- **Two-model architecture**: auxiliary analysis + dialog model for intelligent context understanding
- **Persistent data storage** with SQLite and graceful degradation
- **In-memory session state** with message history
- **Prompt store** with dynamic context and scenario-based responses
- **Robust error handling** and graceful degradation
- **Automatic database migrations** and cleanup
- **Logging** to `/log/app.log`
- **Docker support** with persistent data volumes

## Requirements
- Python 3.12
- `uv` for dependency management
- Telegram bot token and OpenRouter API key

## Installation

### Method 1: From Repository (Recommended)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/easy-lessons-bot.git
   cd easy-lessons-bot
   ```

2. **Install dependencies:**
   ```bash
   # Install Python 3.12 and uv if not already installed
   # Then install project dependencies
   uv sync
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your tokens (see Environment variables section)
   ```

4. **Run the bot:**
   ```bash
   make run
   ```

### Method 2: Docker Only

1. **Create a directory for the bot:**
   ```bash
   mkdir ~/easy-lessons-bot
   cd ~/easy-lessons-bot
   ```

2. **Create environment file:**
   ```bash
   cat > .env << 'EOF'
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
   OPENROUTER_API_KEY=your_openrouter_api_key_here
   EOF
   ```

3. **Edit the .env file:**
   Open `.env` in your text editor and replace the placeholder values with your actual tokens:
   - Get Telegram Bot Token from [@BotFather](https://t.me/BotFather)
   - Get OpenRouter API Key from [OpenRouter](https://openrouter.ai/)

4. **Run the bot:**
   ```bash
   docker pull yourusername/easy-lessons-bot:latest
   docker run -d \
     --name easy-lessons-bot \
     --env-file .env \
     -p 8001:8001 \
     -v ./log:/log \
     -v ./data:/app/data \
     yourusername/easy-lessons-bot:latest
   ```

5. **Check if it's working:**
   ```bash
   # View logs
   docker logs -f easy-lessons-bot
   
   # Check status
   docker ps
   ```

## Environment variables
- `TELEGRAM_BOT_TOKEN` (required) - Telegram bot token from BotFather
- `OPENROUTER_API_KEY` (required) - OpenRouter API key for LLM access
- `OPENROUTER_MODEL` (default: `gpt-4o-mini`) - OpenRouter model to use
- `LLM_TEMPERATURE` (default: `0.9`) - LLM temperature parameter (0.0-2.0)
- `LLM_MAX_TOKENS` (default: `6000`) - Maximum tokens for LLM response
- `HISTORY_LIMIT` (default: `30`) - Maximum number of messages to keep in history
- `DATABASE_ENABLED` (default: `true`) - Enable database persistence
- `DATABASE_PATH` (default: `data/bot.db`) - Path to SQLite database file
- `DATABASE_CLEANUP_HOURS` (default: `168`) - Hours after which to cleanup old sessions (7 days)

## Architecture

### Two-Model Flow
The bot uses a sophisticated two-model architecture:

1. **Auxiliary Model**: Analyzes context and determines:
   - Current scenario (discussion, explanation, unknown)
   - Topic identification
   - Understanding level (0-9)
   - Whether it's a new question or topic

2. **Dialog Model**: Generates responses based on:
   - System prompts with dynamic context
   - Scenario-specific prompts
   - User's understanding level
   - Conversation history

### Data Persistence
- **SQLite database** for persistent storage
- **Graceful degradation**: Falls back to in-memory storage if database is unavailable
- **Automatic migrations**: Database schema updates automatically
- **Session cleanup**: Old sessions are automatically cleaned up
- **Repository pattern**: Clean separation of data access logic

## Development

### Code Quality
```bash
# Lint code
make lint

# Format code
make fmt

# Run tests
make test
```

### Available Commands
View all available commands:
```bash
make help
```

This shows all development, Docker, and utility commands with descriptions.

## Docker

### Quick Start
Copy environment file and run:
```bash
cp .env.example .env
# Edit .env with your tokens
make docker-compose-up
```

### Docker Commands

#### Single Container
```bash
# Build image
make docker-build

# Build with custom tag
make docker-build-tag

# Run container
make docker-run

# Stop container
make docker-stop

# View logs
make docker-logs

# Clean up Docker system
make docker-clean
```

#### Docker Compose (Recommended)
```bash
# Production mode
make docker-compose-up

# Development mode (with live reloading)
make docker-compose-dev

# Stop all services
make docker-compose-down

# View logs
make docker-compose-logs

# Restart services
make docker-compose-restart
```

### Environment Setup
1. Copy example environment file:
   ```bash
   cp .env.example .env
   ```
2. Edit `.env` with your actual tokens:
   - `TELEGRAM_BOT_TOKEN` - from BotFather
   - `OPENROUTER_API_KEY` - from OpenRouter

## Pre-commit
Install hooks and run:
```bash
uv run pre-commit install
uv run pre-commit run -a
```
Pytest runs via pre-commit at push time (configured in `.pre-commit-config.yaml`).

## Project structure
See `doc/vision.md` for architecture and tech vision.

## Usage examples
- Start the bot in Telegram and send:
  - "Новая тема" — to begin a new topic.
  - "Объясни дроби простыми словами" — the bot explains fractions simply.
  - "Почему небо голубое?" — the bot answers and may ask a follow-up.
- The bot adapts explanations to a child-friendly style and keeps short dialog history (up to 30 messages).
- **Persistent sessions**: Your conversation history is saved and restored between bot restarts.
- **Intelligent context**: The bot remembers your understanding level and adapts explanations accordingly.
