"""Telegram bot handlers for Easy Lessons Bot."""

import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

logger = logging.getLogger(__name__)

# Create router for handlers
router = Router()


@router.message(Command("start"))
async def start_command(message: Message) -> None:
    """Handle /start command."""
    logger.info("Received /start command from user %s", message.from_user.id)

    welcome_text = (
        "👋 Привет! Я Easy Lessons Bot - твой помощник в изучении новых тем!\n\n"
        "🎯 Я помогу тебе разобраться с любой темой простым и понятным языком.\n"
        "💡 Просто напиши мне, что хочешь изучить, и я объясню это доступно!\n\n"
        "📚 Готов начать обучение? Напиши мне название темы!"
    )

    await message.answer(welcome_text)
    logger.info("Sent welcome message to user %s", message.from_user.id)


@router.message()
async def handle_text_message(message: Message) -> None:
    """Handle text messages from users."""
    logger.info("Received text message from user %s: %s",
                message.from_user.id, message.text[:50])

    # TODO: Implement LLM integration in future iterations
    response_text = (
        "🤖 Пока я только учусь! В следующих итерациях я смогу "
        "отвечать на твои вопросы с помощью ИИ.\n\n"
        "📝 Твое сообщение: " + message.text
    )

    await message.answer(response_text)
    logger.info("Sent response to user %s", message.from_user.id)
