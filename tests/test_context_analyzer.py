"""Tests for ContextAnalyzer class."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.context.context_analyzer import ContextAnalyzer
from core.session_state import SessionState


class TestContextAnalyzer:
    """Test cases for ContextAnalyzer."""

    @pytest.fixture
    def mock_session(self):
        """Create mock session for testing."""
        session = MagicMock(spec=SessionState)
        session.chat_id = 12345
        session.understanding_level = 5
        session.previous_understanding_level = 4
        session.topic = "math"
        session.previous_topic = "science"
        session.user_preferences = ["visual", "examples"]
        session.get_recent_messages.return_value = [
            MagicMock(role="user", content="Hello"),
            MagicMock(role="bot", content="Hi there!"),
        ]
        return session

    @pytest.fixture
    def mock_llm_client(self):
        """Create mock LLM client."""
        client = MagicMock()
        client.generate_response = AsyncMock()
        return client

    def test_context_analyzer_initialization(self):
        """Test ContextAnalyzer initialization."""
        analyzer = ContextAnalyzer()
        assert analyzer._llm_client is None

    def test_context_analyzer_initialization_with_client(self, mock_llm_client):
        """Test ContextAnalyzer initialization with LLM client."""
        analyzer = ContextAnalyzer(mock_llm_client)
        assert analyzer._llm_client is mock_llm_client

    @pytest.mark.asyncio
    async def test_analyze_context_with_auxiliary_model_success(
        self, mock_session, mock_llm_client
    ):
        """Test successful context analysis with auxiliary model."""
        # Mock LLM response
        mock_response = '{"scenario": "discussion", "topic": "math", "question": "What is 2+2?", "is_new_question": true, "is_new_topic": false, "understanding_level": 5, "previous_understanding_level": 4, "previous_topic": "science", "user_preferences": ["visual"]}'
        mock_llm_client.generate_response.return_value = mock_response

        analyzer = ContextAnalyzer(mock_llm_client)
        result = await analyzer.analyze_context_with_auxiliary_model(
            mock_session, "What is 2+2?"
        )

        # Verify result
        assert result["scenario"] == "discussion"
        assert result["topic"] == "math"
        assert result["question"] == "What is 2+2?"
        assert result["is_new_question"] is True
        assert result["is_new_topic"] is False
        assert result["understanding_level"] == 5
        assert result["previous_understanding_level"] == 4
        assert result["previous_topic"] == "science"
        assert result["user_preferences"] == ["visual"]

        # Verify LLM client was called correctly
        mock_llm_client.generate_response.assert_called_once()
        call_args = mock_llm_client.generate_response.call_args
        assert call_args[1]["temperature"] == 0.1
        assert call_args[1]["max_tokens"] == 200

    @pytest.mark.asyncio
    async def test_analyze_context_with_auxiliary_model_invalid_json(
        self, mock_session, mock_llm_client
    ):
        """Test context analysis with invalid JSON response."""
        # Mock LLM response with invalid JSON
        mock_llm_client.generate_response.return_value = "Invalid JSON response"

        analyzer = ContextAnalyzer(mock_llm_client)
        result = await analyzer.analyze_context_with_auxiliary_model(
            mock_session, "Test message"
        )

        # Should return fallback context
        assert result["scenario"] == "unknown"
        assert result["topic"] == "math"  # From session
        assert result["question"] is None
        assert result["is_new_question"] is False
        assert result["is_new_topic"] is False

    @pytest.mark.asyncio
    async def test_analyze_context_with_auxiliary_model_llm_error(
        self, mock_session, mock_llm_client
    ):
        """Test context analysis with LLM error."""
        # Mock LLM error
        mock_llm_client.generate_response.side_effect = Exception("LLM error")

        with patch("core.graceful_degradation.get_graceful_degradation_manager") as mock_degradation:
            mock_degradation_manager = MagicMock()
            mock_degradation_manager.handle_auxiliary_model_failure.return_value = {
                "scenario": "unknown",
                "topic": "fallback",
                "question": None,
                "is_new_question": False,
                "is_new_topic": False,
                "understanding_level": 5,
                "previous_understanding_level": 4,
                "previous_topic": "science",
                "user_preferences": [],
            }
            mock_degradation.return_value = mock_degradation_manager

            analyzer = ContextAnalyzer(mock_llm_client)
            result = await analyzer.analyze_context_with_auxiliary_model(
                mock_session, "Test message"
            )

            # Should use graceful degradation
            assert result["scenario"] == "unknown"
            assert result["topic"] == "fallback"
            mock_degradation_manager.handle_auxiliary_model_failure.assert_called_once_with(
                mock_session, "Test message"
            )

    def test_get_fallback_context(self, mock_session):
        """Test fallback context generation."""
        analyzer = ContextAnalyzer()
        result = analyzer._get_fallback_context(mock_session)

        assert result["scenario"] == "unknown"
        assert result["topic"] == "math"
        assert result["question"] is None
        assert result["is_new_question"] is False
        assert result["is_new_topic"] is False
        assert result["understanding_level"] == 5
        assert result["previous_understanding_level"] == 4
        assert result["previous_topic"] == "science"
        assert result["user_preferences"] == ["visual", "examples"]

    @pytest.mark.asyncio
    async def test_identify_topic_with_llm_success(self, mock_session, mock_llm_client):
        """Test successful topic identification."""
        mock_llm_client.generate_response.return_value = "math"
        available_topics = ["math", "science", "reading"]

        analyzer = ContextAnalyzer(mock_llm_client)
        result = await analyzer.identify_topic_with_llm(
            mock_session, "What is 2+2?", available_topics
        )

        assert result == "math"

    @pytest.mark.asyncio
    async def test_identify_topic_with_llm_invalid_topic(self, mock_session, mock_llm_client):
        """Test topic identification with invalid topic."""
        mock_llm_client.generate_response.return_value = "invalid_topic"
        available_topics = ["math", "science", "reading"]

        analyzer = ContextAnalyzer(mock_llm_client)
        result = await analyzer.identify_topic_with_llm(
            mock_session, "Test message", available_topics
        )

        assert result == "unknown"

    @pytest.mark.asyncio
    async def test_identify_topic_with_llm_error(self, mock_session, mock_llm_client):
        """Test topic identification with LLM error."""
        mock_llm_client.generate_response.side_effect = Exception("LLM error")
        available_topics = ["math", "science", "reading"]

        analyzer = ContextAnalyzer(mock_llm_client)
        result = await analyzer.identify_topic_with_llm(
            mock_session, "Test message", available_topics
        )

        assert result == "unknown"
