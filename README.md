# Easy Lessons Bot

A Telegram bot for simple, friendly explanations powered by an LLM (OpenRouter via OpenAI SDK).

## Features
- Aiogram 3 (long polling)
- Two-model flow: auxiliary analysis + dialog model
- In-memory session state with message history
- Prompt store with dynamic context
- Robust error handling and graceful degradation
- Logging to `/log/app.log`

## Requirements
- Python 3.12
- `uv` for dependency management
- Telegram bot token and OpenRouter API key

## Quickstart (local)
1. Install Python 3.12 and `uv`.
2. Install deps:
   ```bash
   uv sync
   ```
3. Configure environment:
   - Create `.env` with variables below
4. Run bot:
   ```bash
   make run
   ```

## Environment variables
- `TELEGRAM_BOT_TOKEN` (required)
- `OPENROUTER_API_KEY` (required)
- `OPENROUTER_MODEL` (default: `gpt-4o-mini`)
- `LLM_TEMPERATURE` (default: `0.9`)
- `LLM_MAX_TOKENS` (default: `6000`)
- `HISTORY_LIMIT` (default: `30`)

## Development
- Lint:
  ```bash
  make lint
  ```
- Format:
  ```bash
  make fmt
  ```
- Tests:
  ```bash
  make test
  ```

## Docker
Build image:
```bash
make docker-build
```
Run container (expects env file with required variables):
```bash
make docker-run
```

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
