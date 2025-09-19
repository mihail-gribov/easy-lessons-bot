"""Global bot instance management."""

import logging
from typing import Optional

from aiogram import Bot

logger = logging.getLogger(__name__)

# Global bot instance
_bot_instance: Optional[Bot] = None


def set_bot_instance(bot: Bot) -> None:
    """Set global bot instance."""
    global _bot_instance
    _bot_instance = bot
    logger.info("Global bot instance set")


def get_bot_instance() -> Optional[Bot]:
    """Get global bot instance."""
    return _bot_instance


def clear_bot_instance() -> None:
    """Clear global bot instance."""
    global _bot_instance
    _bot_instance = None
    logger.info("Global bot instance cleared")
