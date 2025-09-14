"""Unified message processor for handling all types of messages."""

import logging
from typing import Any, Dict, Optional

from aiogram.types import Message

from core.context_processor import process_aux_result
from core.error_messages import get_user_friendly_error_message
from core.llm_client import LLMError, get_llm_client
from core.prompt_store import get_prompt_store
from core.session_state import get_session_manager

logger = logging.getLogger(__name__)


class UnifiedMessageProcessor:
    """Unified processor for all message types (text, voice, photo, document)."""

    def __init__(self):
        """Initialize unified message processor."""
        self.session_manager = get_session_manager()
        self.prompt_store = get_prompt_store()
        self.llm_client = get_llm_client()

    async def process_message(
        self, message: Message, message_type: str = "text"
    ) -> Optional[str]:
        """
        Process any type of message through unified pipeline.

        Args:
            message: Telegram message object
            message_type: Type of message ('text', 'voice', 'photo', 'document')

        Returns:
            Response text or None if error
        """
        chat_id = message.chat.id
        logger.info(
            "Processing %s message from user %s", message_type, chat_id
        )

        try:
            # Get session state
            session = await self.session_manager.get_session(chat_id)

            # Extract content based on message type
            content = await self._extract_message_content(message, message_type)
            if not content:
                return "Извините, не удалось обработать ваше сообщение."

            # Add user message to session history
            session.add_message("user", content)

            # Two-model flow: auxiliary analysis → context processing → dialog model
            aux = await self.prompt_store.analyze_context_with_auxiliary_model(
                session, content
            )
            dynamic_ctx = process_aux_result(session, aux)

            # Build messages for dialog model
            messages = self.prompt_store.build_dialog_context(
                session, dynamic_ctx, content
            )

            # Generate response with graceful degradation
            try:
                response_text = await self.llm_client.generate_response(
                    messages=messages,
                    temperature=0.3,
                    max_tokens=512,
                )
            except LLMError as e:
                logger.warning("Dialog model failed, using graceful degradation: %s", e)
                from core.graceful_degradation import get_graceful_degradation_manager

                degradation_manager = get_graceful_degradation_manager()
                response_text = degradation_manager.handle_dialog_model_failure(
                    session, content
                )

            # Add bot response to session history
            session.add_message("assistant", response_text)

            # Save session to persistence
            await self.session_manager.save_session(session)

            logger.info("Successfully processed %s message from user %s", message_type, chat_id)
            return response_text

        except LLMError as e:
            logger.exception("LLM error processing %s message from user %s", message_type, chat_id)
            return get_user_friendly_error_message(e)

        except Exception as e:
            logger.exception("Unexpected error processing %s message from user %s", message_type, chat_id)
            return get_user_friendly_error_message(e)

    async def _extract_message_content(
        self, message: Message, message_type: str
    ) -> Optional[str]:
        """
        Extract content from message based on type.

        Args:
            message: Telegram message object
            message_type: Type of message

        Returns:
            Extracted content or None if failed
        """
        if message_type == "text":
            return message.text or ""

        elif message_type == "voice":
            return await self._transcribe_voice_message(message)

        elif message_type in ("photo", "document"):
            return await self._extract_media_content(message, message_type)

        else:
            logger.warning("Unknown message type: %s", message_type)
            return None

    async def _transcribe_voice_message(self, message: Message) -> Optional[str]:
        """
        Transcribe voice message to text.

        Args:
            message: Telegram message object with voice

        Returns:
            Transcribed text or None if failed
        """
        try:
            # Import here to avoid circular imports
            from bot.handlers import media_handlers

            if not media_handlers:
                logger.error("Media handlers not initialized for transcription")
                return None

            # Get current session context
            session = await self.session_manager.get_session(message.chat.id)
            session_context = session.to_dict() if session else {}

            # Process audio to get transcript
            result = await media_handlers.media_processor.process_media(
                file_id=message.voice.file_id,
                file_type="voice",
                chat_id=str(message.chat.id),
                session_context=session_context,
            )

            if "error" in result:
                logger.error("Audio transcription error: %s", result["error"])
                return None

            transcript = result.get("transcript", "")
            if not transcript:
                logger.warning("No transcript returned from audio processing")
                return None

            logger.info("Audio transcribed successfully: %s", transcript[:100])
            return transcript

        except Exception as e:
            logger.error("Error transcribing voice message: %s", e, exc_info=True)
            return None

    async def _extract_media_content(
        self, message: Message, message_type: str
    ) -> Optional[str]:
        """
        Extract content from media message (photo/document).

        Args:
            message: Telegram message object
            message_type: Type of media ('photo' or 'document')

        Returns:
            Extracted content or None if failed
        """
        try:
            # Import here to avoid circular imports
            from bot.handlers import media_handlers

            if not media_handlers:
                logger.error("Media handlers not initialized for media processing")
                return None

            # Get current session context
            session = await self.session_manager.get_session(message.chat.id)
            session_context = session.to_dict() if session else {}

            # Determine file_id and file_type based on message type
            if message_type == "photo":
                photo = message.photo[-1] if message.photo else None
                if not photo:
                    return None
                file_id = photo.file_id
                file_type = "photo"
            elif message_type == "document":
                document = message.document
                if not document or not document.mime_type or not document.mime_type.startswith("image/"):
                    return "Извините, я пока поддерживаю только изображения."
                file_id = document.file_id
                file_type = "image"
            else:
                return None

            # Process media
            result = await media_handlers.media_processor.process_media(
                file_id=file_id,
                file_type=file_type,
                chat_id=str(message.chat.id),
                session_context=session_context,
            )

            if "error" in result:
                logger.error("Media processing error: %s", result["error"])
                return None

            # Extract text content
            extracted_text = result.get("extracted_text", "")
            content_type = result.get("content_type", message_type)

            if extracted_text:
                content = f"[{content_type}] {extracted_text}"
                logger.info("Media content extracted: %s", content[:100])
                return content
            else:
                return f"[{content_type}] Изображение получено"

        except Exception as e:
            logger.error("Error extracting media content: %s", e, exc_info=True)
            return None

    def _create_synthetic_message(
        self, transcript: str, original_message: Message
    ) -> Message:
        """
        Create synthetic message object from transcript.

        Args:
            transcript: Transcribed text
            original_message: Original message object

        Returns:
            Synthetic message object with transcript as text
        """
        # Create a copy of the original message with transcript as text
        synthetic_message = original_message.model_copy(
            update={
                'text': transcript,
                'voice': None,
                'photo': None,
                'document': None,
                'content_type': 'text'
            }
        )
        return synthetic_message


# Global unified message processor instance
_unified_processor: Optional[UnifiedMessageProcessor] = None


def get_unified_processor() -> UnifiedMessageProcessor:
    """Get global unified message processor instance."""
    global _unified_processor  # noqa: PLW0603
    if _unified_processor is None:
        _unified_processor = UnifiedMessageProcessor()
    return _unified_processor
