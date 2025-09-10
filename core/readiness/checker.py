"""Readiness checker ensures bot dependencies are available."""

from __future__ import annotations

from settings.config import get_settings


async def check_bot_readiness() -> tuple[bool, str]:
    """Validate essential configuration and basic environment.

    Returns:
        (is_ready, reason)
    """
    try:
        settings = get_settings()
        if not settings.telegram_bot_token:
            return False, "Missing TELEGRAM_BOT_TOKEN"
        if not settings.openrouter_api_key:
            return False, "Missing OPENROUTER_API_KEY"
        if not settings.openrouter_model:
            return False, "Missing OPENROUTER_MODEL"
    except Exception as e:
        return False, f"Settings error: {e}"

    # Network/LLM ping is optional in MVP to avoid delays on /start
    return True, "OK"
