"""Tests for unified message processor functionality."""

import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram.types import Chat, Message, User, Voice, PhotoSize

from core.llm_client import LLMTimeoutError


class TestUnifiedMessageProcessor:
    """Test cases for unified message processor."""

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
    def mock_voice_message(self):
        """Create mock voice message."""
        user = User(id=12345, is_bot=False, first_name="Test", username="testuser")
        chat = Chat(id=67890, type="private")
        
        # Create voice object
        voice = Voice(
            file_id="voice_file_id",
            file_unique_id="voice_unique_id",
            duration=5,
            mime_type="audio/ogg",
            file_size=1024
        )
        
        message = Message(
            message_id=1,
            from_user=user,
            chat=chat,
            date=datetime.datetime.now(datetime.UTC),
            content_type="voice",
            text=None,
            voice=voice,
        )
        return message

    @pytest.fixture
    def mock_photo_message(self):
        """Create mock photo message."""
        user = User(id=12345, is_bot=False, first_name="Test", username="testuser")
        chat = Chat(id=67890, type="private")
        
        # Create photo object
        photo = PhotoSize(
            file_id="photo_file_id",
            file_unique_id="photo_unique_id",
            width=800,
            height=600,
            file_size=1024
        )
        
        message = Message(
            message_id=1,
            from_user=user,
            chat=chat,
            date=datetime.datetime.now(datetime.UTC),
            content_type="photo",
            text=None,
            photo=[photo],
        )
        return message

    @pytest.mark.asyncio
    async def test_process_text_message_success(self, mock_message):
        """Test successful text message processing."""
        with (
            patch("core.service_registry.get_session_manager") as mock_session_manager,
            patch("core.service_registry.get_prompt_store") as mock_prompt_store,
            patch("core.service_registry.get_llm_client") as mock_llm_client,
            patch("core.message_processor.process_aux_result") as mock_process_aux,
        ):
            # Mock session
            mock_session = MagicMock()
            mock_session_manager.return_value.get_session = AsyncMock(
                return_value=mock_session
            )
            mock_session_manager.return_value.save_session = AsyncMock()

            # Mock prompt store
            mock_store = MagicMock()
            mock_store.analyze_context_with_auxiliary_model = AsyncMock(
                return_value={"scenario": "discussion", "topic": "test"}
            )
            mock_store.build_dialog_context.return_value = [
                {"role": "user", "content": "test"}
            ]
            mock_prompt_store.return_value = mock_store

            # Mock LLM client
            mock_client = MagicMock()
            mock_client.generate_response = AsyncMock(return_value="Test response")
            mock_llm_client.return_value = mock_client

            # Mock context processor
            mock_process_aux.return_value = {"scenario": "discussion", "topic": "test"}

            # Import and test processor
            from core.message_processor import UnifiedMessageProcessor

            processor = UnifiedMessageProcessor()
            result = await processor.process_message(mock_message, "text")

            # Verify calls
            assert result == "Test response"
            mock_session.add_message.assert_any_call("user", "Test message")
            mock_session.add_message.assert_called_with("assistant", "Test response")
            mock_session_manager.return_value.save_session.assert_called_once_with(
                mock_session
            )

    @pytest.mark.asyncio
    async def test_process_text_message_llm_error_with_graceful_degradation(
        self, mock_message
    ):
        """Test text message processing with LLM error and graceful degradation."""
        with (
            patch("core.service_registry.get_session_manager") as mock_session_manager,
            patch("core.service_registry.get_prompt_store") as mock_prompt_store,
            patch("core.service_registry.get_llm_client") as mock_llm_client,
            patch("core.message_processor.process_aux_result") as mock_process_aux,
            patch(
                "core.service_registry.get_graceful_degradation_manager"
            ) as mock_degradation,
        ):
            # Mock session
            mock_session = MagicMock()
            mock_session_manager.return_value.get_session = AsyncMock(
                return_value=mock_session
            )
            mock_session_manager.return_value.save_session = AsyncMock()

            # Mock prompt store
            mock_store = MagicMock()
            mock_store.analyze_context_with_auxiliary_model = AsyncMock(
                return_value={"scenario": "discussion", "topic": "test"}
            )
            mock_store.build_dialog_context.return_value = [
                {"role": "user", "content": "test"}
            ]
            mock_prompt_store.return_value = mock_store

            # Mock LLM client to raise error
            mock_client = MagicMock()
            mock_client.generate_response = AsyncMock(
                side_effect=LLMTimeoutError("Timeout")
            )
            mock_llm_client.return_value = mock_client

            # Mock context processor
            mock_process_aux.return_value = {"scenario": "discussion", "topic": "test"}

            # Mock graceful degradation
            mock_degradation_manager = MagicMock()
            mock_degradation_manager.handle_dialog_model_failure.return_value = (
                "Fallback response"
            )
            mock_degradation.return_value = mock_degradation_manager

            # Import and test processor
            from core.message_processor import UnifiedMessageProcessor

            processor = UnifiedMessageProcessor()
            result = await processor.process_message(mock_message, "text")

            # Verify calls
            assert result == "Fallback response"
            mock_degradation_manager.handle_dialog_model_failure.assert_called_once_with(
                mock_session, "Test message"
            )
            mock_session.add_message.assert_called_with(
                "assistant", "Fallback response"
            )

    @pytest.mark.asyncio
    async def test_process_voice_message_success(self, mock_voice_message):
        """Test successful voice message processing."""
        with (
            patch("core.service_registry.get_session_manager") as mock_session_manager,
            patch("core.service_registry.get_prompt_store") as mock_prompt_store,
            patch("core.service_registry.get_llm_client") as mock_llm_client,
            patch("core.message_processor.process_aux_result") as mock_process_aux,
            patch("bot.handlers.media_handlers") as mock_media_handlers,
        ):
            # Mock session
            mock_session = MagicMock()
            mock_session.to_dict.return_value = {"chat_id": "67890"}
            mock_session_manager.return_value.get_session = AsyncMock(
                return_value=mock_session
            )
            mock_session_manager.return_value.save_session = AsyncMock()

            # Mock media handlers
            mock_media_processor = MagicMock()
            mock_media_processor.process_media = AsyncMock(
                return_value={"transcript": "Transcribed text"}
            )
            mock_media_handlers.media_processor = mock_media_processor

            # Mock prompt store
            mock_store = MagicMock()
            mock_store.analyze_context_with_auxiliary_model = AsyncMock(
                return_value={"scenario": "discussion", "topic": "test"}
            )
            mock_store.build_dialog_context.return_value = [
                {"role": "user", "content": "test"}
            ]
            mock_prompt_store.return_value = mock_store

            # Mock LLM client
            mock_client = MagicMock()
            mock_client.generate_response = AsyncMock(return_value="Voice response")
            mock_llm_client.return_value = mock_client

            # Mock context processor
            mock_process_aux.return_value = {"scenario": "discussion", "topic": "test"}

            # Import and test processor
            from core.message_processor import UnifiedMessageProcessor

            processor = UnifiedMessageProcessor()
            result = await processor.process_message(mock_voice_message, "voice")

            # Verify calls
            assert result == "Voice response"
            mock_media_processor.process_media.assert_called_once_with(
                file_id="voice_file_id",
                file_type="voice",
                chat_id="67890",
                session_context={"chat_id": "67890"},
            )
            mock_session.add_message.assert_any_call("user", "Transcribed text")

    @pytest.mark.asyncio
    async def test_process_voice_message_transcription_failed(self, mock_voice_message):
        """Test voice message processing when transcription fails."""
        with (
            patch("core.service_registry.get_session_manager") as mock_session_manager,
            patch("bot.handlers.media_handlers") as mock_media_handlers,
        ):
            # Mock session
            mock_session = MagicMock()
            mock_session.to_dict.return_value = {"chat_id": "67890"}
            mock_session_manager.return_value.get_session = AsyncMock(
                return_value=mock_session
            )

            # Mock media handlers to return error
            mock_media_processor = MagicMock()
            mock_media_processor.process_media = AsyncMock(
                return_value={"error": "Transcription failed"}
            )
            mock_media_handlers.media_processor = mock_media_processor

            # Import and test processor
            from core.message_processor import UnifiedMessageProcessor

            processor = UnifiedMessageProcessor()
            result = await processor.process_message(mock_voice_message, "voice")

            # Verify result - should return error message when transcription fails
            assert result == "Извините, не удалось обработать ваше сообщение."

    @pytest.mark.asyncio
    async def test_process_photo_message_success(self, mock_photo_message):
        """Test successful photo message processing."""
        with (
            patch("core.service_registry.get_session_manager") as mock_session_manager,
            patch("core.service_registry.get_prompt_store") as mock_prompt_store,
            patch("core.service_registry.get_llm_client") as mock_llm_client,
            patch("core.message_processor.process_aux_result") as mock_process_aux,
            patch("bot.handlers.media_handlers") as mock_media_handlers,
        ):
            # Mock session
            mock_session = MagicMock()
            mock_session.to_dict.return_value = {"chat_id": "67890"}
            mock_session_manager.return_value.get_session = AsyncMock(
                return_value=mock_session
            )
            mock_session_manager.return_value.save_session = AsyncMock()

            # Mock media handlers
            mock_media_processor = MagicMock()
            mock_media_processor.process_media = AsyncMock(
                return_value={
                    "extracted_text": "Image content",
                    "content_type": "photo"
                }
            )
            mock_media_handlers.media_processor = mock_media_processor

            # Mock prompt store
            mock_store = MagicMock()
            mock_store.analyze_context_with_auxiliary_model = AsyncMock(
                return_value={"scenario": "discussion", "topic": "test"}
            )
            mock_store.build_dialog_context.return_value = [
                {"role": "user", "content": "test"}
            ]
            mock_prompt_store.return_value = mock_store

            # Mock LLM client
            mock_client = MagicMock()
            mock_client.generate_response = AsyncMock(return_value="Photo response")
            mock_llm_client.return_value = mock_client

            # Mock context processor
            mock_process_aux.return_value = {"scenario": "discussion", "topic": "test"}

            # Import and test processor
            from core.message_processor import UnifiedMessageProcessor

            processor = UnifiedMessageProcessor()
            result = await processor.process_message(mock_photo_message, "photo")

            # Verify calls
            assert result == "Photo response"
            mock_media_processor.process_media.assert_called_once_with(
                file_id="photo_file_id",
                file_type="photo",
                chat_id="67890",
                session_context={"chat_id": "67890"},
            )
            mock_session.add_message.assert_any_call(
                "user", "[photo] Image content"
            )

    @pytest.mark.asyncio
    async def test_extract_message_content_unknown_type(self, mock_message):
        """Test message content extraction with unknown message type."""
        from core.message_processor import UnifiedMessageProcessor

        processor = UnifiedMessageProcessor()
        result = await processor._extract_message_content(mock_message, "unknown")

        assert result is None

    @pytest.mark.asyncio
    async def test_create_synthetic_message(self, mock_voice_message):
        """Test creation of synthetic message from transcript."""
        from core.message_processor import UnifiedMessageProcessor

        processor = UnifiedMessageProcessor()
        synthetic = processor._create_synthetic_message(
            "Transcribed text", mock_voice_message
        )

        assert synthetic.text == "Transcribed text"
        assert synthetic.voice is None
        assert synthetic.photo is None
        assert synthetic.document is None
        assert synthetic.content_type == "text"
