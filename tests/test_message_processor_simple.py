"""Simplified tests for unified message processor functionality."""

import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram.types import Chat, Message, User, Voice, PhotoSize

from core.llm_client import LLMTimeoutError


class TestUnifiedMessageProcessorSimple:
    """Simplified test cases for unified message processor."""

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

    @pytest.mark.asyncio
    async def test_process_text_message_success(self, mock_message):
        """Test successful text message processing."""
        # Mock all dependencies at module level
        with (
            patch("core.message_processor.get_session_manager") as mock_session_manager,
            patch("core.message_processor.get_prompt_store") as mock_prompt_store,
            patch("core.message_processor.get_llm_client") as mock_llm_client,
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
            patch("core.message_processor.get_session_manager") as mock_session_manager,
            patch("core.message_processor.get_prompt_store") as mock_prompt_store,
            patch("core.message_processor.get_llm_client") as mock_llm_client,
            patch("core.message_processor.process_aux_result") as mock_process_aux,
            patch("core.graceful_degradation.get_graceful_degradation_manager") as mock_degradation,
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
    async def test_extract_message_content_unknown_type(self, mock_message):
        """Test message content extraction with unknown message type."""
        with patch("core.message_processor.get_session_manager") as mock_session_manager:
            mock_session_manager.return_value = MagicMock()
            
            from core.message_processor import UnifiedMessageProcessor

            processor = UnifiedMessageProcessor()
            result = await processor._extract_message_content(mock_message, "unknown")

            assert result is None

    @pytest.mark.asyncio
    async def test_create_synthetic_message(self, mock_message):
        """Test creation of synthetic message from transcript."""
        with patch("core.message_processor.get_session_manager") as mock_session_manager:
            mock_session_manager.return_value = MagicMock()
            
            from core.message_processor import UnifiedMessageProcessor

            processor = UnifiedMessageProcessor()
            synthetic = processor._create_synthetic_message(
                "Transcribed text", mock_message
            )

            assert synthetic.text == "Transcribed text"
            assert synthetic.voice is None
            assert synthetic.photo is None
            assert synthetic.document is None
            assert synthetic.content_type == "text"
