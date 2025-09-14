"""Telegram bot handlers for Easy Lessons Bot."""

import logging
from typing import Optional

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from core.context_processor import process_aux_result
from core.error_messages import get_user_friendly_error_message
from core.llm_client import LLMError, get_llm_client
from core.prompt_store import get_prompt_store
from core.readiness.checker import check_bot_readiness
from core.session_state import get_session_manager
from core.version_info import format_version_info
from core.welcome_messages import get_random_welcome_message
from bot.media_handlers import MediaHandlers

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


@router.message(Command("version"))
async def version_command(message: Message) -> None:
    """Handle /version command."""
    logger.info("Received /version command from user %s", message.from_user.id)

    try:
        version_info = format_version_info()
        response = (
            f"🤖 <b>Easy Lessons Bot</b>\n\n"
            f"📊 <b>Информация о версии:</b>\n<code>{version_info}</code>"
        )
        await message.answer(response, parse_mode="HTML")
        logger.info("Sent version info to user %s", message.from_user.id)
    except Exception:
        logger.exception("Error getting version info for user %s", message.from_user.id)
        await message.answer("❌ Не удалось получить информацию о версии.")


@router.message(lambda message: message.text is not None)
async def handle_text_message(message: Message) -> None:
    """Handle text messages from users."""
    chat_id = message.chat.id
    user_text = message.text or ""

    logger.info("💬 Received text message from user %s: %s", chat_id, user_text[:50])

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


# Initialize media handlers (will be set with bot instance in main.py)
media_handlers: Optional[MediaHandlers] = None


def initialize_media_handlers(bot) -> None:
    """Initialize media handlers with bot instance."""
    global media_handlers
    logger.info("Initializing media handlers with bot instance")
    media_handlers = MediaHandlers(bot)
    logger.info("Media handlers initialized successfully")


@router.message(lambda message: message.voice is not None)
async def handle_voice_message(message: Message) -> None:
    """Handle voice messages by transcribing and passing to text pipeline."""
    chat_id = message.chat.id
    logger.info("🎤 VOICE MESSAGE RECEIVED from user %s", chat_id)
    logger.info("Voice message details: file_id=%s, duration=%s", 
                message.voice.file_id if message.voice else "None",
                message.voice.duration if message.voice else "None")

    if not media_handlers:
        logger.error("Media handlers not initialized")
        await message.answer("Извините, медиа-обработка недоступна.")
        return

    try:
        # Transcribe audio using media handlers
        transcript = await _transcribe_voice_message(message)
        
        if not transcript:
            await message.answer("Извините, не удалось распознать голосовое сообщение.")
            return
            
        logger.info("🎯 Audio transcribed: %s", transcript[:100])
        
        # Process transcript directly through the text message pipeline
        # Create a temporary message object with the transcript as text
        temp_message = message.model_copy(update={'text': transcript, 'voice': None, 'content_type': 'text'})
        await handle_text_message(temp_message)
        
    except Exception as e:
        logger.exception("Error handling voice message from user %s", chat_id)
        await message.answer("Извините, произошла ошибка при обработке голосового сообщения.")


@router.message(lambda message: message.photo is not None)
async def handle_photo_message(message: Message) -> None:
    """Handle photo messages from users."""
    chat_id = message.chat.id
    logger.info("Received photo message from user %s", chat_id)

    if not media_handlers:
        logger.error("Media handlers not initialized")
        await message.answer("Извините, медиа-обработка недоступна.")
        return

    try:
        response = await media_handlers.handle_photo_message(message, None)
        if response:
            await message.answer(response)
            logger.info("Sent photo response to user %s", chat_id)
        else:
            await message.answer("Извините, не удалось обработать изображение.")
    except Exception as e:
        logger.exception("Error handling photo message from user %s", chat_id)
        await message.answer("Извините, произошла ошибка при обработке изображения.")


@router.message(lambda message: message.document is not None)
async def handle_document_message(message: Message) -> None:
    """Handle document messages from users."""
    chat_id = message.chat.id
    logger.info("Received document message from user %s", chat_id)

    if not media_handlers:
        logger.error("Media handlers not initialized")
        await message.answer("Извините, медиа-обработка недоступна.")
        return

    try:
        response = await media_handlers.handle_document_message(message, None)
        if response:
            await message.answer(response)
            logger.info("Sent document response to user %s", chat_id)
        else:
            await message.answer("Извините, не удалось обработать документ.")
    except Exception as e:
        logger.exception("Error handling document message from user %s", chat_id)
        await message.answer("Извините, произошла ошибка при обработке документа.")


# Debug handler removed - it was blocking all other handlers


async def _transcribe_voice_message(message: Message) -> Optional[str]:
    """
    Transcribe voice message using media handlers.
    
    Args:
        message: Telegram message object with voice
        
    Returns:
        Transcribed text or None if failed
    """
    try:
        if not media_handlers:
            logger.error("Media handlers not initialized for transcription")
            return None
            
        # Get current session context
        session_manager = get_session_manager()
        session = await session_manager.get_session(message.chat.id)
        session_context = session.to_dict() if session else {}
        
        # Process audio to get transcript
        result = await media_handlers.media_processor.process_media(
            file_id=message.voice.file_id,
            file_type="voice",
            chat_id=str(message.chat.id),
            session_context=session_context,
        )
        
        if "error" in result:
            logger.error(f"Audio transcription error: {result['error']}")
            return None
            
        transcript = result.get("transcript", "")
        if not transcript:
            logger.warning("No transcript returned from audio processing")
            return None
            
        return transcript
        
    except Exception as e:
        logger.error(f"Error transcribing voice message: {e}", exc_info=True)
        return None


