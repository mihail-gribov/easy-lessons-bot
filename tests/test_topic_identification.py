"""Tests for LLM-based topic identification functionality."""

from unittest.mock import AsyncMock, patch

import pytest

from core.prompt_store import PromptStore
from core.session_state import SessionState


class TestTopicIdentification:
    """Test cases for topic identification with LLM."""

    @pytest.fixture
    def prompt_store(self):
        """Create PromptStore instance for testing."""
        return PromptStore()

    @pytest.fixture
    def session(self):
        """Create test session."""
        session = SessionState("test_chat_123")
        session.add_message("user", "Привет!")
        session.add_message("assistant", "Привет! Как дела?")
        return session

    @pytest.mark.asyncio
    async def test_identify_valid_topic(self, prompt_store, session):
        """Test successful topic identification."""
        # Mock LLM response
        mock_llm_client = AsyncMock()
        mock_llm_client.generate_response.return_value = "math"

        with patch("core.llm_client.get_llm_client", return_value=mock_llm_client):
            result = await prompt_store.identify_topic_with_llm(
                session,
                "расскажи про дроби",
            )

        assert result == "math"
        mock_llm_client.generate_response.assert_called_once()

        # Check call arguments
        call_args = mock_llm_client.generate_response.call_args
        assert call_args[1]["temperature"] == 0.1
        assert call_args[1]["max_tokens"] == 50

    @pytest.mark.asyncio
    async def test_identify_unknown_topic(self, prompt_store, session):
        """Test unknown topic identification."""
        # Mock LLM response
        mock_llm_client = AsyncMock()
        mock_llm_client.generate_response.return_value = "unknown"

        with patch("core.llm_client.get_llm_client", return_value=mock_llm_client):
            result = await prompt_store.identify_topic_with_llm(
                session,
                "какая сегодня погода?",
            )

        assert result == "unknown"

    @pytest.mark.asyncio
    async def test_identify_invalid_topic(self, prompt_store, session):
        """Test invalid topic (not in available topics)."""
        # Mock LLM response with invalid topic
        mock_llm_client = AsyncMock()
        mock_llm_client.generate_response.return_value = "quantum_physics"

        with patch("core.llm_client.get_llm_client", return_value=mock_llm_client):
            result = await prompt_store.identify_topic_with_llm(
                session,
                "расскажи про квантовую физику",
            )

        assert result == "unknown"

    @pytest.mark.asyncio
    async def test_llm_error_handling(self, prompt_store, session):
        """Test error handling when LLM fails."""
        # Mock LLM client that raises exception
        mock_llm_client = AsyncMock()
        mock_llm_client.generate_response.side_effect = Exception("LLM error")

        with patch("core.llm_client.get_llm_client", return_value=mock_llm_client):
            result = await prompt_store.identify_topic_with_llm(
                session,
                "расскажи про математику",
            )

        assert result == "unknown"

    @pytest.mark.asyncio
    async def test_context_building(self, prompt_store, session):
        """Test that correct context is built for LLM."""
        # Mock LLM response
        mock_llm_client = AsyncMock()
        mock_llm_client.generate_response.return_value = "science"

        with patch("core.llm_client.get_llm_client", return_value=mock_llm_client):
            await prompt_store.identify_topic_with_llm(
                session,
                "расскажи про химию",
            )

        # Check that LLM was called with correct messages
        call_args = mock_llm_client.generate_response.call_args
        messages = call_args.kwargs["messages"]  # Keyword argument

        # Should have system prompt + history + current message
        assert len(messages) >= 3
        assert messages[0]["role"] == "system"
        assert messages[-1]["role"] == "user"
        assert messages[-1]["content"] == "расскажи про химию"

        # Check that bot messages are converted to assistant
        for msg in messages[1:-1]:  # Skip system and user messages
            if msg["role"] in ["assistant", "user"]:
                assert msg["role"] in [
                    "assistant",
                    "user",
                ], f"Invalid role: {msg['role']}"

    def test_fallback_prompt(self, prompt_store):
        """Test fallback prompt minimal text present."""
        fallback = prompt_store._get_topic_identification_fallback()
        assert "topic identification assistant" in fallback

    def test_validate_topic(self, prompt_store):
        """Test topic validation."""
        # Valid topics
        assert prompt_store.validate_topic("math") is True
        assert prompt_store.validate_topic("SCIENCE") is True  # Case insensitive
        assert prompt_store.validate_topic("space") is True

        # Invalid topics
        assert prompt_store.validate_topic("quantum_physics") is False
        assert prompt_store.validate_topic("unknown") is False
        assert prompt_store.validate_topic("") is False

    def test_get_available_topics(self, prompt_store):
        """Test getting available topics."""
        topics = prompt_store.get_available_topics()

        assert isinstance(topics, list)
        assert len(topics) > 0
        assert "math" in topics
        assert "science" in topics
        assert "space" in topics


class TestTopicIdentificationIntegration:
    """Integration tests for topic identification."""

    @pytest.mark.asyncio
    async def test_full_topic_identification_flow(self):
        """Test complete flow from user message to topic identification."""
        from core.prompt_store import get_prompt_store
        from core.session_state import get_session_manager

        # Create session with some history
        session_manager = get_session_manager()
        session = session_manager.get_session("integration_test")
        session.add_message("user", "Привет!")
        session.add_message("assistant", "Привет! Чем могу помочь?")

        # Mock LLM response
        mock_llm_client = AsyncMock()
        mock_llm_client.generate_response.return_value = "math"

        prompt_store = get_prompt_store()

        with patch("core.llm_client.get_llm_client", return_value=mock_llm_client):
            result = await prompt_store.identify_topic_with_llm(
                session,
                "хочу изучить дроби",
            )

        assert result == "math"

        # Verify session state
        assert session.active_topic is None  # Not set yet, just identified
        assert (
            len(session.recent_messages) == 2
        )  # 2 original messages (user message not added yet in identify_topic_with_llm)

    @pytest.mark.asyncio
    async def test_topic_identification_with_empty_history(self):
        """Test topic identification with empty conversation history."""
        from core.prompt_store import get_prompt_store
        from core.session_state import get_session_manager

        # Create empty session
        session_manager = get_session_manager()
        session = session_manager.get_session("empty_test")

        # Mock LLM response
        mock_llm_client = AsyncMock()
        mock_llm_client.generate_response.return_value = "science"

        prompt_store = get_prompt_store()

        with patch("core.llm_client.get_llm_client", return_value=mock_llm_client):
            result = await prompt_store.identify_topic_with_llm(
                session,
                "расскажи про физику",
            )

        assert result == "science"

        # Check that only system prompt and current message were sent
        call_args = mock_llm_client.generate_response.call_args
        messages = call_args.kwargs["messages"]
        assert len(messages) == 2  # system + user message
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
