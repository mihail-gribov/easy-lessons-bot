"""Tests for refactored bot handlers functionality."""

import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram.types import Chat, Message, User, Voice, PhotoSize, Document

from core.llm_client import LLMTimeoutError


class TestRefactoredBotHandlers:
    """Test cases for refactored bot handlers."""

    @pytest.fixture
    def mock_message(self):
        """Create mock Telegram message."""
        user = User(id=12345, is_bot=False, first_name="Test", username="testuser")
        chat = Chat(id=67890, type="private")
        message = Message(
            message_id=1,
            from_user=user,
            chat=chat,
            date=datetime.datetime.now(datetime.UTC),
            content_type="text",
            text="Test message",
        )
        return message

    @pytest.fixture
    def mock_start_message(self):
        """Create mock /start command message."""
        user = User(id=12345, is_bot=False, first_name="Test", username="testuser")
        chat = Chat(id=67890, type="private")
        message = Message(
            message_id=1,
            from_user=user,
            chat=chat,
            date=datetime.datetime.now(datetime.UTC),
            content_type="text",
            text="/start",
        )
        return message

    @pytest.mark.asyncio
    async def test_start_command_bot_ready(self, mock_start_message):
        """Test /start command when bot is ready."""
        with (
            patch("bot.handlers.check_bot_readiness") as mock_readiness,
            patch("bot.handlers.get_random_welcome_message") as mock_welcome,
            patch(
                "aiogram.types.message.Message.answer", new_callable=AsyncMock
            ) as mock_answer,
        ):
            # Mock bot readiness
            mock_readiness.return_value = (True, None)
            mock_welcome.return_value = "Welcome message"

            # Import and call handler
            from bot.handlers import start_command

            await start_command(mock_start_message)

            # Verify calls
            mock_readiness.assert_called_once()
            mock_welcome.assert_called_once()
            mock_answer.assert_called_once_with("Welcome message")

    @pytest.mark.asyncio
    async def test_start_command_bot_not_ready(self, mock_start_message):
        """Test /start command when bot is not ready."""
        with (
            patch("bot.handlers.check_bot_readiness") as mock_readiness,
            patch("bot.handlers.get_random_welcome_message") as mock_welcome,
            patch(
                "aiogram.types.message.Message.answer", new_callable=AsyncMock
            ) as mock_answer,
        ):
            # Mock bot not ready
            mock_readiness.return_value = (False, "LLM unavailable")

            # Import and call handler
            from bot.handlers import start_command

            await start_command(mock_start_message)

            # Verify calls
            mock_readiness.assert_called_once()
            mock_welcome.assert_not_called()
            mock_answer.assert_called_once_with(
                "Бот временно недоступен. Пожалуйста, попробуйте позже."
            )

    @pytest.mark.asyncio
    async def test_handle_text_message_success(self, mock_message):
        """Test successful text message handling with unified processor."""
        with (
            patch("bot.handlers.get_unified_processor") as mock_processor,
            patch(
                "aiogram.types.message.Message.answer", new_callable=AsyncMock
            ) as mock_answer,
        ):
            # Mock unified processor
            mock_processor_instance = MagicMock()
            mock_processor_instance.process_message = AsyncMock(
                return_value="Test response"
            )
            mock_processor.return_value = mock_processor_instance

            # Import and call handler
            from bot.handlers import handle_text_message

            await handle_text_message(mock_message)

            # Verify calls
            mock_processor_instance.process_message.assert_called_once_with(
                mock_message, "text"
            )
            mock_answer.assert_called_once_with("Test response")

    @pytest.mark.asyncio
    async def test_handle_text_message_processor_error(self, mock_message):
        """Test text message handling when processor returns None."""
        with (
            patch("bot.handlers.get_unified_processor") as mock_processor,
            patch(
                "aiogram.types.message.Message.answer", new_callable=AsyncMock
            ) as mock_answer,
        ):
            # Mock unified processor to return None (error case)
            mock_processor_instance = MagicMock()
            mock_processor_instance.process_message = AsyncMock(return_value=None)
            mock_processor.return_value = mock_processor_instance

            # Import and call handler
            from bot.handlers import handle_text_message

            await handle_text_message(mock_message)

            # Verify calls
            mock_processor_instance.process_message.assert_called_once_with(
                mock_message, "text"
            )
            mock_answer.assert_called_once_with(
                "Извините, произошла ошибка при обработке сообщения."
            )

    @pytest.mark.asyncio
    async def test_handle_voice_message_success(self):
        """Test successful voice message handling with unified processor."""
        # Create voice message with proper Voice object
        user = User(id=12345, is_bot=False, first_name="Test", username="testuser")
        chat = Chat(id=67890, type="private")
        
        voice = Voice(
            file_id="voice_file_id",
            file_unique_id="voice_unique_id",
            duration=5,
            mime_type="audio/ogg",
            file_size=1024
        )
        
        voice_message = Message(
            message_id=1,
            from_user=user,
            chat=chat,
            date=datetime.datetime.now(datetime.UTC),
            content_type="voice",
            text=None,
            voice=voice,
        )

        with (
            patch("bot.handlers.get_unified_processor") as mock_processor,
            patch(
                "aiogram.types.message.Message.answer", new_callable=AsyncMock
            ) as mock_answer,
        ):
            # Mock unified processor
            mock_processor_instance = MagicMock()
            mock_processor_instance.process_message = AsyncMock(
                return_value="Voice response"
            )
            mock_processor.return_value = mock_processor_instance

            # Import and call handler
            from bot.handlers import handle_voice_message

            await handle_voice_message(voice_message)

            # Verify calls
            mock_processor_instance.process_message.assert_called_once_with(
                voice_message, "voice"
            )
            mock_answer.assert_called_once_with("Voice response")

    @pytest.mark.asyncio
    async def test_handle_voice_message_processor_error(self):
        """Test voice message handling when processor returns None."""
        # Create voice message with proper Voice object
        user = User(id=12345, is_bot=False, first_name="Test", username="testuser")
        chat = Chat(id=67890, type="private")
        
        voice = Voice(
            file_id="voice_file_id",
            file_unique_id="voice_unique_id",
            duration=5,
            mime_type="audio/ogg",
            file_size=1024
        )
        
        voice_message = Message(
            message_id=1,
            from_user=user,
            chat=chat,
            date=datetime.datetime.now(datetime.UTC),
            content_type="voice",
            text=None,
            voice=voice,
        )

        with (
            patch("bot.handlers.get_unified_processor") as mock_processor,
            patch(
                "aiogram.types.message.Message.answer", new_callable=AsyncMock
            ) as mock_answer,
        ):
            # Mock unified processor to return None (error case)
            mock_processor_instance = MagicMock()
            mock_processor_instance.process_message = AsyncMock(return_value=None)
            mock_processor.return_value = mock_processor_instance

            # Import and call handler
            from bot.handlers import handle_voice_message

            await handle_voice_message(voice_message)

            # Verify calls
            mock_processor_instance.process_message.assert_called_once_with(
                voice_message, "voice"
            )
            mock_answer.assert_called_once_with(
                "Извините, не удалось обработать голосовое сообщение."
            )

    @pytest.mark.asyncio
    async def test_handle_photo_message_success(self):
        """Test successful photo message handling with unified processor."""
        # Create photo message with proper PhotoSize object
        user = User(id=12345, is_bot=False, first_name="Test", username="testuser")
        chat = Chat(id=67890, type="private")
        
        photo = PhotoSize(
            file_id="photo_file_id",
            file_unique_id="photo_unique_id",
            width=800,
            height=600,
            file_size=1024
        )
        
        photo_message = Message(
            message_id=1,
            from_user=user,
            chat=chat,
            date=datetime.datetime.now(datetime.UTC),
            content_type="photo",
            text=None,
            photo=[photo],
        )

        with (
            patch("bot.handlers.get_unified_processor") as mock_processor,
            patch(
                "aiogram.types.message.Message.answer", new_callable=AsyncMock
            ) as mock_answer,
        ):
            # Mock unified processor
            mock_processor_instance = MagicMock()
            mock_processor_instance.process_message = AsyncMock(
                return_value="Photo response"
            )
            mock_processor.return_value = mock_processor_instance

            # Import and call handler
            from bot.handlers import handle_photo_message

            await handle_photo_message(photo_message)

            # Verify calls
            mock_processor_instance.process_message.assert_called_once_with(
                photo_message, "photo"
            )
            mock_answer.assert_called_once_with("Photo response")

    @pytest.mark.asyncio
    async def test_handle_document_message_success(self):
        """Test successful document message handling with unified processor."""
        # Create document message with proper Document object
        user = User(id=12345, is_bot=False, first_name="Test", username="testuser")
        chat = Chat(id=67890, type="private")
        
        document = Document(
            file_id="doc_file_id",
            file_unique_id="doc_unique_id",
            file_name="test.jpg",
            mime_type="image/jpeg",
            file_size=1024
        )
        
        document_message = Message(
            message_id=1,
            from_user=user,
            chat=chat,
            date=datetime.datetime.now(datetime.UTC),
            content_type="document",
            text=None,
            document=document,
        )

        with (
            patch("bot.handlers.get_unified_processor") as mock_processor,
            patch(
                "aiogram.types.message.Message.answer", new_callable=AsyncMock
            ) as mock_answer,
        ):
            # Mock unified processor
            mock_processor_instance = MagicMock()
            mock_processor_instance.process_message = AsyncMock(
                return_value="Document response"
            )
            mock_processor.return_value = mock_processor_instance

            # Import and call handler
            from bot.handlers import handle_document_message

            await handle_document_message(document_message)

            # Verify calls
            mock_processor_instance.process_message.assert_called_once_with(
                document_message, "document"
            )
            mock_answer.assert_called_once_with("Document response")
