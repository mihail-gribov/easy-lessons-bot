"""Main entry point for the Easy Lessons Bot application."""

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.handlers import initialize_media_handlers, router
from core.logging_config import setup_logging
from core.persistence import close_database, initialize_database, initialize_migrations
from core.service_registry import initialize_services

# Import version utilities
from core.version_info import format_version_info
from settings.config import get_settings


async def main() -> None:
    """Main application entry point."""
    # Set up logging
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("Easy Lessons Bot starting up...")
    logger.info("Bot info: %s", format_version_info())
    logger.info("Logging configured successfully")

    # Load configuration
    try:
        settings = get_settings()
        logger.info("Configuration loaded successfully")
        logger.info("Using model: %s", settings.openrouter_model)
        logger.info("History limit: %s", settings.history_limit)
        logger.info("Database enabled: %s", settings.database_enabled)
        if settings.database_enabled:
            logger.info("Database path: %s", settings.database_path)
    except ValueError:
        logger.exception("Failed to load configuration")
        logger.exception("Please check your environment variables or .env file")
        sys.exit(1)

    # Initialize services in DI container
    try:
        initialize_services()
        logger.info("Services initialized in DI container successfully")
    except Exception:
        logger.exception("Failed to initialize services")
        sys.exit(1)

    # Initialize database and migrations
    try:
        await initialize_database()
        await initialize_migrations()
        logger.info("Database and migrations initialized successfully")
    except Exception:
        logger.exception("Failed to initialize database")
        logger.exception("Bot will continue with in-memory storage")

    # Initialize bot
    bot = Bot(
        token=settings.telegram_bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    # Initialize media handlers with bot instance first
    initialize_media_handlers(bot)

    # Initialize dispatcher
    dp = Dispatcher()
    dp.include_router(router)

    logger.info("Bot initialized successfully")

    try:
        # Start polling
        logger.info("Starting bot polling...")
        await dp.start_polling(bot)
    except Exception:
        logger.exception("Error during bot polling")
    finally:
        await bot.session.close()
        await close_database()
        logger.info("Bot stopped")


if __name__ == "__main__":
    asyncio.run(main())
