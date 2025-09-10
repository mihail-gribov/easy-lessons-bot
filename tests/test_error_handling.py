"""Tests for error handling and graceful degradation."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from core.llm_client import (
    LLMClient,
    LLMError,
    LLMTimeoutError,
    LLMRateLimitError,
    LLMConnectionError,
    LLMAPIError,
)
from core.error_messages import ErrorMessageStore, get_user_friendly_error_message
from core.graceful_degradation import GracefulDegradationManager
from core.session_state import SessionState


class TestLLMClientErrorHandling:
    """Test LLM client error handling."""
    
    @pytest.fixture
    def llm_client(self):
        """Create LLM client for testing."""
        with patch('core.llm_client.get_settings') as mock_settings:
            mock_settings.return_value.telegram_bot_token = "test_token"
            mock_settings.return_value.openrouter_api_key = "test_key"
            mock_settings.return_value.openrouter_model = "test_model"
            mock_settings.return_value.llm_temperature = 0.9
            mock_settings.return_value.llm_max_tokens = 1000
            return LLMClient()
    
    @pytest.mark.asyncio
    async def test_timeout_error_handling(self, llm_client):
        """Test timeout error handling."""
        import asyncio
        
        # Mock client to raise timeout error
        llm_client.client.chat.completions.create = AsyncMock(
            side_effect=asyncio.TimeoutError("Request timeout")
        )
        
        messages = [{"role": "user", "content": "test"}]
        
        with pytest.raises(LLMTimeoutError):
            await llm_client.generate_response(messages)
    
    @pytest.mark.asyncio
    async def test_rate_limit_error_handling(self, llm_client):
        """Test rate limit error handling."""
        # Mock client to raise rate limit error
        llm_client.client.chat.completions.create = AsyncMock(
            side_effect=Exception("Rate limit exceeded")
        )
        
        messages = [{"role": "user", "content": "test"}]
        
        with pytest.raises(LLMError):
            await llm_client.generate_response(messages)
    
    @pytest.mark.asyncio
    async def test_connection_error_handling(self, llm_client):
        """Test connection error handling with retry."""
        # Mock client to raise connection error on first attempt, succeed on second
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "test response"
        mock_response.usage = None
        
        llm_client.client.chat.completions.create = AsyncMock(
            side_effect=[
                Exception("Connection failed"),
                mock_response
            ]
        )
        
        messages = [{"role": "user", "content": "test"}]
        
        # Should succeed after retry
        response = await llm_client.generate_response(messages)
        assert response == "test response"
        assert llm_client.client.chat.completions.create.call_count == 2
    
    @pytest.mark.asyncio
    async def test_api_error_handling(self, llm_client):
        """Test API error handling."""
        # Mock client to raise API error
        llm_client.client.chat.completions.create = AsyncMock(
            side_effect=Exception("API error")
        )
        
        messages = [{"role": "user", "content": "test"}]
        
        with pytest.raises(LLMError):
            await llm_client.generate_response(messages)


class TestErrorMessageStore:
    """Test error message store."""
    
    def test_timeout_error_message(self):
        """Test timeout error message."""
        store = ErrorMessageStore()
        error = LLMTimeoutError("Timeout")
        message = store.get_error_message(error)
        
        assert "время" in message.lower() or "думаю" in message.lower() or "задумался" in message.lower()
        assert "😔" in message or "⏰" in message or "🕐" in message or "⏱️" in message
    
    def test_rate_limit_error_message(self):
        """Test rate limit error message."""
        store = ErrorMessageStore()
        error = LLMRateLimitError("Rate limit")
        message = store.get_error_message(error)
        
        assert "много" in message.lower() or "подожди" in message.lower()
        assert "🚦" in message or "⏳" in message or "🔄" in message
    
    def test_connection_error_message(self):
        """Test connection error message."""
        store = ErrorMessageStore()
        error = LLMConnectionError("Connection failed")
        message = store.get_error_message(error)
        
        assert "интернет" in message.lower() or "подключ" in message.lower()
        assert "🌐" in message or "📡" in message or "🔌" in message
    
    def test_generic_error_message(self):
        """Test generic error message."""
        store = ErrorMessageStore()
        error = Exception("Generic error")
        message = store.get_error_message(error)
        
        assert "проблем" in message.lower() or "извини" in message.lower() or "пошло" in message.lower() or "упс" in message.lower()
        assert "😔" in message or "🤷" in message or "😅" in message
    
    def test_get_user_friendly_error_message(self):
        """Test global function."""
        error = LLMTimeoutError("Timeout")
        message = get_user_friendly_error_message(error)
        
        assert isinstance(message, str)
        assert len(message) > 0


class TestGracefulDegradation:
    """Test graceful degradation mechanisms."""
    
    @pytest.fixture
    def session(self):
        """Create test session."""
        return SessionState(chat_id=12345)
    
    @pytest.fixture
    def degradation_manager(self):
        """Create degradation manager."""
        return GracefulDegradationManager()
    
    def test_auxiliary_model_failure_handling(self, degradation_manager, session):
        """Test auxiliary model failure handling."""
        user_message = "What is photosynthesis?"
        
        context = degradation_manager.handle_auxiliary_model_failure(session, user_message)
        
        assert isinstance(context, dict)
        assert "scenario" in context
        assert "topic" in context
        assert "question" in context
        assert "is_new_question" in context
        assert "is_new_topic" in context
        assert "understanding_level" in context
    
    def test_dialog_model_failure_handling(self, degradation_manager, session):
        """Test dialog model failure handling."""
        user_message = "Tell me about space"
        session.topic = "space"
        
        response = degradation_manager.handle_dialog_model_failure(session, user_message)
        
        assert isinstance(response, str)
        assert len(response) > 0
        assert "space" in response.lower()
    
    def test_dialog_model_failure_no_topic(self, degradation_manager, session):
        """Test dialog model failure handling without topic."""
        user_message = "Hello"
        
        response = degradation_manager.handle_dialog_model_failure(session, user_message)
        
        assert isinstance(response, str)
        assert len(response) > 0
    
    def test_prompt_loading_failure_handling(self, degradation_manager):
        """Test prompt loading failure handling."""
        fallback = degradation_manager.handle_prompt_loading_failure("system_base")
        
        assert isinstance(fallback, str)
        assert len(fallback) > 0
        assert "assistant" in fallback.lower()
    
    def test_new_topic_detection_heuristic(self, degradation_manager, session):
        """Test new topic detection heuristic."""
        session.topic = "math"
        
        # Test with topic change indicators
        assert degradation_manager._detect_new_topic_heuristic(
            session, "давай о животных"
        )
        assert degradation_manager._detect_new_topic_heuristic(
            session, "расскажи о космосе"
        )
        
        # Test without topic change indicators
        assert not degradation_manager._detect_new_topic_heuristic(
            session, "как решить уравнение"
        )
    
    def test_new_question_detection_heuristic(self, degradation_manager, session):
        """Test new question detection heuristic."""
        # Test with question mark
        assert degradation_manager._detect_new_question_heuristic(
            session, "Что такое фотосинтез?"
        )
        
        # Test with question words
        assert degradation_manager._detect_new_question_heuristic(
            session, "как работает двигатель"
        )
        assert degradation_manager._detect_new_question_heuristic(
            session, "почему небо голубое"
        )
        
        # Test without question indicators
        assert not degradation_manager._detect_new_question_heuristic(
            session, "расскажи историю"
        )


class TestErrorHandlingIntegration:
    """Test error handling integration."""
    
    @pytest.mark.asyncio
    async def test_full_error_handling_flow(self):
        """Test complete error handling flow."""
        # This would test the full integration, but requires more complex mocking
        # For now, we'll test that the components work together
        
        # Test that error messages are generated correctly
        error = LLMTimeoutError("Timeout")
        message = get_user_friendly_error_message(error)
        assert isinstance(message, str)
        assert len(message) > 0
        
        # Test that graceful degradation works
        manager = GracefulDegradationManager()
        session = SessionState(chat_id=12345)
        context = manager.handle_auxiliary_model_failure(session, "test")
        assert isinstance(context, dict)
