"""Media handlers for processing audio and image messages."""

import logging
from typing import Any, Dict, Optional

from aiogram import Bot, types
from aiogram.fsm.context import FSMContext

from core.audio_handler import AudioHandler
from core.context_matcher import ContextMatcher
from core.image_analyzer import ImageAnalyzer
from core.media_processor import MediaProcessor
from core.session_state import SessionManager
from settings.config import get_settings

logger = logging.getLogger(__name__)


class MediaHandlers:
    """Handlers for media messages (audio, images)."""

    def __init__(self, bot: Optional[Bot] = None):
        """Initialize media handlers."""
        self.settings = get_settings()
        self.media_processor = MediaProcessor(bot)
        self.audio_handler = AudioHandler()
        self.image_analyzer = ImageAnalyzer()
        self.context_matcher = ContextMatcher()
        self.session_manager = SessionManager()

    async def handle_voice_message(
        self, message: types.Message, state: FSMContext
    ) -> Optional[str]:
        """
        Handle voice message from user.

        Args:
            message: Telegram message object
            state: FSM context

        Returns:
            Response text or None if error
        """
        try:
            chat_id = str(message.chat.id)
            logger.info(f"Processing voice message from chat {chat_id}")

            # Get current session context
            session = await self.session_manager.get_session(chat_id)
            session_context = session.to_dict() if session else {}

            # Process audio
            result = await self.media_processor.process_media(
                file_id=message.voice.file_id,
                file_type="voice",
                chat_id=chat_id,
                session_context=session_context,
            )

            if "error" in result:
                logger.error(f"Media processing error: {result['error']}")
                return f"Извините, не удалось обработать голосовое сообщение: {result['error']}"

            # Analyze intent from transcript
            transcript = result.get("transcript", "")
            if transcript:
                intent_result = await self.audio_handler.analyze_audio_intent(
                    transcript, session_context
                )
                result.update(intent_result)

            # Match with context
            context_result = await self.context_matcher.match_context(
                result, session_context
            )

            # Update session with media context
            if session:
                session.add_message("user", f"[Голосовое сообщение] {transcript}")
                await self.session_manager.save_session(session)

            # Generate response based on analysis
            response = await self._generate_media_response(
                result, context_result, session_context
            )

            return response

        except Exception as e:
            logger.error(f"Error handling voice message: {e}", exc_info=True)
            return "Извините, произошла ошибка при обработке голосового сообщения."

    async def handle_photo_message(
        self, message: types.Message, state: FSMContext
    ) -> Optional[str]:
        """
        Handle photo message from user.

        Args:
            message: Telegram message object
            state: FSM context

        Returns:
            Response text or None if error
        """
        try:
            chat_id = str(message.chat.id)
            logger.info(f"Processing photo message from chat {chat_id}")

            # Get current session context
            session = await self.session_manager.get_session(chat_id)
            session_context = session.to_dict() if session else {}

            # Use the highest quality photo
            photo = message.photo[-1] if message.photo else None
            if not photo:
                return "Извините, не удалось получить изображение."

            # Process image
            result = await self.media_processor.process_media(
                file_id=photo.file_id,
                file_type="photo",
                chat_id=chat_id,
                session_context=session_context,
            )

            if "error" in result:
                logger.error(f"Media processing error: {result['error']}")
                return f"Извините, не удалось обработать изображение: {result['error']}"

            # Match with context
            context_result = await self.context_matcher.match_context(
                result, session_context
            )

            # Update session with media context
            if session:
                extracted_text = result.get("extracted_text", "")
                content_type = result.get("content_type", "image")
                session.add_message(
                    "user", f"[Изображение: {content_type}] {extracted_text}"
                )
                await self.session_manager.save_session(session)

            # Generate response based on analysis
            response = await self._generate_media_response(
                result, context_result, session_context
            )

            return response

        except Exception as e:
            logger.error(f"Error handling photo message: {e}", exc_info=True)
            return "Извините, произошла ошибка при обработке изображения."

    async def handle_document_message(
        self, message: types.Message, state: FSMContext
    ) -> Optional[str]:
        """
        Handle document message from user.

        Args:
            message: Telegram message object
            state: FSM context

        Returns:
            Response text or None if error
        """
        try:
            chat_id = str(message.chat.id)
            document = message.document

            # Check if it's an image document
            if document.mime_type and document.mime_type.startswith("image/"):
                logger.info(f"Processing image document from chat {chat_id}")

                # Get current session context
                session = await self.session_manager.get_session(chat_id)
                session_context = session.to_dict() if session else {}

                # Process as image
                result = await self.media_processor.process_media(
                    file_id=document.file_id,
                    file_type="image",
                    chat_id=chat_id,
                    session_context=session_context,
                )

                if "error" in result:
                    logger.error(f"Media processing error: {result['error']}")
                    return f"Извините, не удалось обработать изображение: {result['error']}"

                # Match with context
                context_result = await self.context_matcher.match_context(
                    result, session_context
                )

                # Update session with media context
                if session:
                    extracted_text = result.get("extracted_text", "")
                    content_type = result.get("content_type", "document")
                    session.add_message(
                        "user", f"[Документ: {content_type}] {extracted_text}"
                    )
                    await self.session_manager.save_session(session)

                # Generate response based on analysis
                response = await self._generate_media_response(
                    result, context_result, session_context
                )

                return response
            else:
                return "Извините, я пока поддерживаю только изображения. Текстовые документы не обрабатываются."

        except Exception as e:
            logger.error(f"Error handling document message: {e}", exc_info=True)
            return "Извините, произошла ошибка при обработке документа."

    async def _generate_media_response(
        self,
        media_result: Dict[str, Any],
        context_result: Dict[str, Any],
        session_context: Dict[str, Any],
    ) -> str:
        """
        Generate response based on media analysis and context.

        Args:
            media_result: Media analysis results
            context_result: Context matching results
            session_context: Current session context

        Returns:
            Generated response text
        """
        try:
            # Check for fallback case (Whisper not available)
            if media_result.get("fallback", False):
                return "Я получил ваше голосовое сообщение, но в данный момент транскрипция аудио недоступна. Пожалуйста, напишите ваш вопрос текстом, и я с радостью помогу!"
            
            media_type = media_result.get("type", "unknown")
            scenario = context_result.get("scenario", "unknown")
            context_relation = context_result.get("context_relation", "unrelated")

            # Generate response based on scenario
            if scenario == "explanation":
                return await self._generate_explanation_response(
                    media_result, context_result
                )
            elif scenario == "discussion":
                return await self._generate_discussion_response(
                    media_result, context_result
                )
            else:
                return await self._generate_general_response(
                    media_result, context_result
                )

        except Exception as e:
            logger.error(f"Error generating media response: {e}", exc_info=True)
            return "Извините, произошла ошибка при генерации ответа."

    async def _generate_explanation_response(
        self, media_result: Dict[str, Any], context_result: Dict[str, Any]
    ) -> str:
        """Generate explanation response for media content."""
        media_type = media_result.get("type", "unknown")
        topic = media_result.get("topic", "неизвестная тема")
        subject = media_result.get("subject", "общая")

        if media_type == "audio":
            transcript = media_result.get("transcript", "")
            return f"Я понял ваш вопрос по аудио: '{transcript}'. Давайте разберем тему '{topic}' по предмету '{subject}' простыми словами."
        elif media_type == "image":
            content_type = media_result.get("content_type", "изображение")
            extracted_text = media_result.get("extracted_text", "")
            if extracted_text:
                return f"Я вижу на изображении: {extracted_text}. Давайте разберем это подробно."
            else:
                return f"Я вижу {content_type} по теме '{topic}'. Давайте разберем это подробно."
        else:
            return f"Давайте разберем тему '{topic}' подробно."

    async def _generate_discussion_response(
        self, media_result: Dict[str, Any], context_result: Dict[str, Any]
    ) -> str:
        """Generate discussion response for media content."""
        media_type = media_result.get("type", "unknown")
        topic = media_result.get("topic", "тема")

        if media_type == "audio":
            transcript = media_result.get("transcript", "")
            return f"Отличный вопрос по аудио: '{transcript}'. Давайте обсудим тему '{topic}' дальше."
        elif media_type == "image":
            content_type = media_result.get("content_type", "изображение")
            return f"Интересное изображение по теме '{topic}'. Давайте обсудим это подробнее."
        else:
            return f"Давайте продолжим обсуждение темы '{topic}'."

    async def _generate_general_response(
        self, media_result: Dict[str, Any], context_result: Dict[str, Any]
    ) -> str:
        """Generate general response for media content."""
        media_type = media_result.get("type", "unknown")

        if media_type == "audio":
            transcript = media_result.get("transcript", "")
            return f"Я получил ваше голосовое сообщение: '{transcript}'. Чем могу помочь?"
        elif media_type == "image":
            content_type = media_result.get("content_type", "изображение")
            return f"Я получил {content_type}. Расскажите, что вы хотели бы узнать об этом?"
        else:
            return "Я получил ваше сообщение. Чем могу помочь?"
