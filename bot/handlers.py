"""Telegram bot handlers for Easy Lessons Bot."""

import logging
from typing import Optional

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from core.readiness.checker import check_bot_readiness
from core.version_info import format_version_info
from core.welcome_messages import get_random_welcome_message
from core.message_processor import get_unified_processor
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

    # Use unified message processor
    processor = get_unified_processor()
    response_text = await processor.process_message(message, "text")
    
    if response_text:
        await message.answer(response_text)
        logger.info("Sent LLM response to user %s", chat_id)
    else:
        await message.answer("Извините, произошла ошибка при обработке сообщения.")


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
    """Handle voice messages by transcribing and passing to unified pipeline."""
    chat_id = message.chat.id
    logger.info("🎤 VOICE MESSAGE RECEIVED from user %s", chat_id)
    logger.info("Voice message details: file_id=%s, duration=%s", 
                message.voice.file_id if message.voice else "None",
                message.voice.duration if message.voice else "None")

    # Use unified message processor
    processor = get_unified_processor()
    response_text = await processor.process_message(message, "voice")
    
    if response_text:
        await message.answer(response_text)
        logger.info("Sent voice response to user %s", chat_id)
    else:
        await message.answer("Извините, не удалось обработать голосовое сообщение.")


@router.message(lambda message: message.photo is not None)
async def handle_photo_message(message: Message) -> None:
    """Handle photo messages from users."""
    chat_id = message.chat.id
    logger.info("📷 Received photo message from user %s", chat_id)

    # Use unified message processor
    processor = get_unified_processor()
    response_text = await processor.process_message(message, "photo")
    
    if response_text:
        await message.answer(response_text)
        logger.info("Sent photo response to user %s", chat_id)
    else:
        await message.answer("Извините, не удалось обработать изображение.")


@router.message(lambda message: message.document is not None)
async def handle_document_message(message: Message) -> None:
    """Handle document messages from users."""
    chat_id = message.chat.id
    logger.info("📄 Received document message from user %s", chat_id)

    # Use unified message processor
    processor = get_unified_processor()
    response_text = await processor.process_message(message, "document")
    
    if response_text:
        await message.answer(response_text)
        logger.info("Sent document response to user %s", chat_id)
    else:
        await message.answer("Извините, не удалось обработать документ.")


# Debug handler removed - it was blocking all other handlers


