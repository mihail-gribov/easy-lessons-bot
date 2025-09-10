"""Tests for bot handlers functionality."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from aiogram.types import Message, User, Chat
from core.llm_client import LLMError, LLMTimeoutError
from core.graceful_degradation import GracefulDegradationManager


class TestBotHandlers:
    """Test cases for bot handlers."""

    @pytest.fixture
    def mock_message(self):
        """Create mock Telegram message."""
        user = User(id=12345, is_bot=False, first_name="Test", username="testuser")
        chat = Chat(id=67890, type="private")
        message = Message(
            message_id=1,
            from_user=user,
            chat=chat,
            date=None,
            content_type="text",
            text="Test message"
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
            date=None,
            content_type="text",
            text="/start"
        )
        return message

    @pytest.mark.asyncio
    async def test_start_command_bot_ready(self, mock_start_message):
        """Test /start command when bot is ready."""
        with patch('bot.handlers.check_bot_readiness') as mock_readiness, \
             patch('bot.handlers.get_random_welcome_message') as mock_welcome, \
             patch.object(mock_start_message, 'answer') as mock_answer:
            
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
        with patch('bot.handlers.check_bot_readiness') as mock_readiness, \
             patch('bot.handlers.get_random_welcome_message') as mock_welcome, \
             patch.object(mock_start_message, 'answer') as mock_answer:
            
            # Mock bot not ready
            mock_readiness.return_value = (False, "LLM unavailable")
            
            # Import and call handler
            from bot.handlers import start_command
            await start_command(mock_start_message)
            
            # Verify calls
            mock_readiness.assert_called_once()
            mock_welcome.assert_not_called()
            mock_answer.assert_called_once_with("Бот временно недоступен. Пожалуйста, попробуйте позже.")

    @pytest.mark.asyncio
    async def test_handle_text_message_success(self, mock_message):
        """Test successful text message handling."""
        with patch('bot.handlers.get_session_manager') as mock_session_manager, \
             patch('bot.handlers.get_prompt_store') as mock_prompt_store, \
             patch('bot.handlers.get_llm_client') as mock_llm_client, \
             patch('bot.handlers.process_aux_result') as mock_process_aux, \
             patch.object(mock_message, 'answer') as mock_answer:
            
            # Mock session
            mock_session = MagicMock()
            mock_session_manager.return_value.get_session.return_value = mock_session
            
            # Mock prompt store
            mock_store = MagicMock()
            mock_store.analyze_context_with_auxiliary_model = AsyncMock(return_value={"topic": "test"})
            mock_store.build_dialog_context.return_value = [{"role": "user", "content": "test"}]
            mock_prompt_store.return_value = mock_store
            
            # Mock LLM client
            mock_client = MagicMock()
            mock_client.generate_response = AsyncMock(return_value="Test response")
            mock_llm_client.return_value = mock_client
            
            # Mock context processor
            mock_process_aux.return_value = {"scenario": "discussion", "topic": "test"}
            
            # Import and call handler
            from bot.handlers import handle_text_message
            await handle_text_message(mock_message)
            
            # Verify calls
            mock_session.add_message.assert_called_with("user", "Test message")
            mock_store.analyze_context_with_auxiliary_model.assert_called_once()
            mock_process_aux.assert_called_once()
            mock_store.build_dialog_context.assert_called_once()
            mock_client.generate_response.assert_called_once()
            mock_session.add_message.assert_called_with("assistant", "Test response")
            mock_answer.assert_called_once_with("Test response")

    @pytest.mark.asyncio
    async def test_handle_text_message_llm_error_with_graceful_degradation(self, mock_message):
        """Test text message handling with LLM error and graceful degradation."""
        with patch('bot.handlers.get_session_manager') as mock_session_manager, \
             patch('bot.handlers.get_prompt_store') as mock_prompt_store, \
             patch('bot.handlers.get_llm_client') as mock_llm_client, \
             patch('bot.handlers.process_aux_result') as mock_process_aux, \
             patch('bot.handlers.get_graceful_degradation_manager') as mock_degradation, \
             patch.object(mock_message, 'answer') as mock_answer:
            
            # Mock session
            mock_session = MagicMock()
            mock_session_manager.return_value.get_session.return_value = mock_session
            
            # Mock prompt store
            mock_store = MagicMock()
            mock_store.analyze_context_with_auxiliary_model = AsyncMock(return_value={"topic": "test"})
            mock_store.build_dialog_context.return_value = [{"role": "user", "content": "test"}]
            mock_prompt_store.return_value = mock_store
            
            # Mock LLM client to raise error
            mock_client = MagicMock()
            mock_client.generate_response = AsyncMock(side_effect=LLMTimeoutError("Timeout"))
            mock_llm_client.return_value = mock_client
            
            # Mock context processor
            mock_process_aux.return_value = {"scenario": "discussion", "topic": "test"}
            
            # Mock graceful degradation
            mock_degradation_manager = MagicMock()
            mock_degradation_manager.handle_dialog_model_failure.return_value = "Fallback response"
            mock_degradation.return_value = mock_degradation_manager
            
            # Import and call handler
            from bot.handlers import handle_text_message
            await handle_text_message(mock_message)
            
            # Verify calls
            mock_client.generate_response.assert_called_once()
            mock_degradation_manager.handle_dialog_model_failure.assert_called_once_with(mock_session, "Test message")
            mock_session.add_message.assert_called_with("assistant", "Fallback response")
            mock_answer.assert_called_once_with("Fallback response")

    @pytest.mark.asyncio
    async def test_handle_text_message_llm_error_with_user_friendly_message(self, mock_message):
        """Test text message handling with LLM error and user-friendly error message."""
        with patch('bot.handlers.get_session_manager') as mock_session_manager, \
             patch('bot.handlers.get_prompt_store') as mock_prompt_store, \
             patch('bot.handlers.get_llm_client') as mock_llm_client, \
             patch('bot.handlers.process_aux_result') as mock_process_aux, \
             patch('bot.handlers.get_graceful_degradation_manager') as mock_degradation, \
             patch('bot.handlers.get_user_friendly_error_message') as mock_error_msg, \
             patch.object(mock_message, 'answer') as mock_answer:
            
            # Mock session
            mock_session = MagicMock()
            mock_session_manager.return_value.get_session.return_value = mock_session
            
            # Mock prompt store
            mock_store = MagicMock()
            mock_store.analyze_context_with_auxiliary_model = AsyncMock(return_value={"topic": "test"})
            mock_store.build_dialog_context.return_value = [{"role": "user", "content": "test"}]
            mock_prompt_store.return_value = mock_store
            
            # Mock LLM client to raise error
            mock_client = MagicMock()
            mock_client.generate_response = AsyncMock(side_effect=LLMTimeoutError("Timeout"))
            mock_llm_client.return_value = mock_client
            
            # Mock context processor
            mock_process_aux.return_value = {"scenario": "discussion", "topic": "test"}
            
            # Mock graceful degradation to also fail
            mock_degradation_manager = MagicMock()
            mock_degradation_manager.handle_dialog_model_failure.side_effect = Exception("Degradation failed")
            mock_degradation.return_value = mock_degradation_manager
            
            # Mock error message
            mock_error_msg.return_value = "Sorry, something went wrong"
            
            # Import and call handler
            from bot.handlers import handle_text_message
            await handle_text_message(mock_message)
            
            # Verify calls
            mock_error_msg.assert_called_once()
            mock_answer.assert_called_once_with("Sorry, something went wrong")

    @pytest.mark.asyncio
    async def test_handle_text_message_unexpected_error(self, mock_message):
        """Test text message handling with unexpected error."""
        with patch('bot.handlers.get_session_manager') as mock_session_manager, \
             patch('bot.handlers.get_user_friendly_error_message') as mock_error_msg, \
             patch.object(mock_message, 'answer') as mock_answer:
            
            # Mock session manager to raise unexpected error
            mock_session_manager.side_effect = Exception("Unexpected error")
            mock_error_msg.return_value = "Sorry, something went wrong"
            
            # Import and call handler
            from bot.handlers import handle_text_message
            await handle_text_message(mock_message)
            
            # Verify calls
            mock_error_msg.assert_called_once()
            mock_answer.assert_called_once_with("Sorry, something went wrong")

    @pytest.mark.asyncio
    async def test_handle_text_message_empty_text(self, mock_message):
        """Test text message handling with empty text."""
        # Set empty text
        mock_message.text = ""
        
        with patch('bot.handlers.get_session_manager') as mock_session_manager, \
             patch('bot.handlers.get_prompt_store') as mock_prompt_store, \
             patch('bot.handlers.get_llm_client') as mock_llm_client, \
             patch('bot.handlers.process_aux_result') as mock_process_aux, \
             patch.object(mock_message, 'answer') as mock_answer:
            
            # Mock session
            mock_session = MagicMock()
            mock_session_manager.return_value.get_session.return_value = mock_session
            
            # Mock prompt store
            mock_store = MagicMock()
            mock_store.analyze_context_with_auxiliary_model = AsyncMock(return_value={"topic": "test"})
            mock_store.build_dialog_context.return_value = [{"role": "user", "content": ""}]
            mock_prompt_store.return_value = mock_store
            
            # Mock LLM client
            mock_client = MagicMock()
            mock_client.generate_response = AsyncMock(return_value="Response to empty message")
            mock_llm_client.return_value = mock_client
            
            # Mock context processor
            mock_process_aux.return_value = {"scenario": "unknown"}
            
            # Import and call handler
            from bot.handlers import handle_text_message
            await handle_text_message(mock_message)
            
            # Verify that empty text was handled
            mock_session.add_message.assert_called_with("user", "")
            mock_answer.assert_called_once_with("Response to empty message")

    @pytest.mark.asyncio
    async def test_handle_text_message_none_text(self, mock_message):
        """Test text message handling with None text."""
        # Set None text
        mock_message.text = None
        
        with patch('bot.handlers.get_session_manager') as mock_session_manager, \
             patch('bot.handlers.get_prompt_store') as mock_prompt_store, \
             patch('bot.handlers.get_llm_client') as mock_llm_client, \
             patch('bot.handlers.process_aux_result') as mock_process_aux, \
             patch.object(mock_message, 'answer') as mock_answer:
            
            # Mock session
            mock_session = MagicMock()
            mock_session_manager.return_value.get_session.return_value = mock_session
            
            # Mock prompt store
            mock_store = MagicMock()
            mock_store.analyze_context_with_auxiliary_model = AsyncMock(return_value={"topic": "test"})
            mock_store.build_dialog_context.return_value = [{"role": "user", "content": ""}]
            mock_prompt_store.return_value = mock_store
            
            # Mock LLM client
            mock_client = MagicMock()
            mock_client.generate_response = AsyncMock(return_value="Response to None message")
            mock_llm_client.return_value = mock_client
            
            # Mock context processor
            mock_process_aux.return_value = {"scenario": "unknown"}
            
            # Import and call handler
            from bot.handlers import handle_text_message
            await handle_text_message(mock_message)
            
            # Verify that None text was handled as empty string
            mock_session.add_message.assert_called_with("user", "")
            mock_answer.assert_called_once_with("Response to None message")

    @pytest.mark.asyncio
    async def test_handle_text_message_with_custom_llm_params(self, mock_message):
        """Test text message handling with custom LLM parameters."""
        with patch('bot.handlers.get_session_manager') as mock_session_manager, \
             patch('bot.handlers.get_prompt_store') as mock_prompt_store, \
             patch('bot.handlers.get_llm_client') as mock_llm_client, \
             patch('bot.handlers.process_aux_result') as mock_process_aux, \
             patch.object(mock_message, 'answer') as mock_answer:
            
            # Mock session
            mock_session = MagicMock()
            mock_session_manager.return_value.get_session.return_value = mock_session
            
            # Mock prompt store
            mock_store = MagicMock()
            mock_store.analyze_context_with_auxiliary_model = AsyncMock(return_value={"topic": "test"})
            mock_store.build_dialog_context.return_value = [{"role": "user", "content": "test"}]
            mock_prompt_store.return_value = mock_store
            
            # Mock LLM client
            mock_client = MagicMock()
            mock_client.generate_response = AsyncMock(return_value="Test response")
            mock_llm_client.return_value = mock_client
            
            # Mock context processor
            mock_process_aux.return_value = {"scenario": "discussion", "topic": "test"}
            
            # Import and call handler
            from bot.handlers import handle_text_message
            await handle_text_message(mock_message)
            
            # Verify that custom parameters were used
            mock_client.generate_response.assert_called_once_with(
                messages=[{"role": "user", "content": "test"}],
                temperature=0.3,
                max_tokens=512,
            )


