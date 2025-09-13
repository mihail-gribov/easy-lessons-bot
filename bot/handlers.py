"""Telegram bot handlers for Easy Lessons Bot."""

import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from core.context_processor import process_aux_result
from core.error_messages import get_user_friendly_error_message
from core.llm_client import LLMError, get_llm_client
from core.prompt_store import get_prompt_store
from core.readiness.checker import check_bot_readiness
from core.session_state import get_session_manager
from core.welcome_messages import get_random_welcome_message

logger = logging.getLogger(__name__)

# Create router for handlers
router = Router()


@router.message(Command("start"))
async def start_command(message: Message) -> None:
    """Handle /start command."""
    logger.info("Received /start command from user %s", message.from_user.id)

    is_ready, reason = await check_bot_readiness()
    if not is_ready:
        await message.answer("Бот временно недоступен. Пожалуйста, попробуйте позже.")
        logger.warning("Bot not ready: %s", reason)
        return

    welcome_text = get_random_welcome_message()
    await message.answer(welcome_text)
    logger.info("Sent welcome message to user %s", message.from_user.id)


@router.message()
async def handle_text_message(message: Message) -> None:
    """Handle text messages from users."""
    chat_id = message.chat.id
    user_text = message.text or ""

    logger.info("Received text message from user %s: %s", chat_id, user_text[:50])

    try:
        # Get session state
        session_manager = get_session_manager()
        session = await session_manager.get_session(chat_id)

        # Add user message to session history
        session.add_message("user", user_text)

        # Two-model flow: auxiliary analysis → context processing → dialog model
        prompt_store = get_prompt_store()

        aux = await prompt_store.analyze_context_with_auxiliary_model(
            session, user_text
        )
        dynamic_ctx = process_aux_result(session, aux)

        # Build messages for dialog model
        messages = prompt_store.build_dialog_context(session, dynamic_ctx, user_text)

        # Generate response with graceful degradation
        llm_client = get_llm_client()
        try:
            response_text = await llm_client.generate_response(
                messages=messages,
                temperature=0.3,
                max_tokens=512,
            )
        except LLMError as e:
            logger.warning("Dialog model failed, using graceful degradation: %s", e)
            from core.graceful_degradation import get_graceful_degradation_manager

            degradation_manager = get_graceful_degradation_manager()
            response_text = degradation_manager.handle_dialog_model_failure(
                session, user_text
            )

        # Add bot response to session history
        session.add_message("assistant", response_text)

        # Save session to persistence
        await session_manager.save_session(session)

        # Send response to user
        await message.answer(response_text)
        logger.info("Sent LLM response to user %s", chat_id)

    except LLMError as e:
        logger.exception("LLM error processing message from user %s", chat_id)
        error_response = get_user_friendly_error_message(e)
        await message.answer(error_response)

    except Exception as e:
        logger.exception("Unexpected error processing message from user %s", chat_id)
        error_response = get_user_friendly_error_message(e)
        await message.answer(error_response)

    # Legacy helpers are removed in the new two-model flow
