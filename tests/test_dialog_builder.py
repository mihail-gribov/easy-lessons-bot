"""Tests for DialogBuilder class."""

from unittest.mock import MagicMock, patch

import pytest

from core.dialog.dialog_builder import DialogBuilder
from core.session_state import SessionState


class TestDialogBuilder:
    """Test cases for DialogBuilder."""

    @pytest.fixture
    def mock_session(self):
        """Create mock session for testing."""
        session = MagicMock(spec=SessionState)
        session.chat_id = 12345
        session.understanding_level = 5
        session.active_topic = "math"
        session.get_recent_messages.return_value = [
            MagicMock(role="user", content="Hello"),
            MagicMock(role="bot", content="Hi there!"),
        ]
        return session

    @pytest.fixture
    def mock_prompt_loader(self):
        """Create mock prompt loader."""
        loader = MagicMock()
        loader.get_system_prompt.return_value = "Test system prompt"
        loader.get_scenario_prompt.return_value = "Test scenario prompt"
        return loader

    def test_dialog_builder_initialization(self):
        """Test DialogBuilder initialization."""
        builder = DialogBuilder()
        assert builder._prompt_loader is None

    def test_dialog_builder_initialization_with_loader(self, mock_prompt_loader):
        """Test DialogBuilder initialization with prompt loader."""
        builder = DialogBuilder(mock_prompt_loader)
        assert builder._prompt_loader is mock_prompt_loader

    def test_build_context_legacy(self, mock_session):
        """Test building legacy context."""
        with patch("core.prompts.prompt_loader.PromptLoader") as mock_loader_class:
            mock_loader = MagicMock()
            mock_loader.get_system_prompt.return_value = "Base system prompt"
            mock_loader_class.return_value = mock_loader

            builder = DialogBuilder()
            result = builder.build_context(mock_session, "Test message", "explanation")

            # Verify structure
            assert len(result) >= 3  # system + history + user message
            assert result[0]["role"] == "system"
            assert result[-1]["role"] == "user"
            assert result[-1]["content"] == "Test message"

    def test_build_context_with_topic(self, mock_session):
        """Test building context with active topic."""
        with patch("core.prompts.prompt_loader.PromptLoader") as mock_loader_class:
            mock_loader = MagicMock()
            mock_loader.get_system_prompt.return_value = "Base system prompt"
            mock_loader_class.return_value = mock_loader

            builder = DialogBuilder()
            result = builder.build_context(mock_session, "Test message")

            # Should have topic context
            system_messages = [msg for msg in result if msg["role"] == "system"]
            assert len(system_messages) >= 2  # base + topic context

    def test_build_dialog_context(self, mock_session):
        """Test building dialog context."""
        with patch("core.prompts.prompt_loader.PromptLoader") as mock_loader_class:
            mock_loader = MagicMock()
            mock_loader.get_system_prompt.return_value = "Base system prompt"
            mock_loader.get_scenario_prompt.return_value = "Scenario prompt"
            mock_loader_class.return_value = mock_loader

            dynamic_ctx = {
                "scenario": "discussion",
                "topic": "math",
                "question": "What is 2+2?",
                "is_new_question": True,
                "is_new_topic": False,
                "understanding_level": 5,
            }

            builder = DialogBuilder()
            result = builder.build_dialog_context(mock_session, dynamic_ctx, "Test message")

            # Verify structure
            assert len(result) >= 2  # system + user message
            assert result[0]["role"] == "system"
            assert result[-1]["role"] == "user"
            assert result[-1]["content"] == "Test message"

            # Verify system prompt contains dynamic context
            system_content = result[0]["content"]
            assert "Context:" in system_content
            assert "scenario: discussion" in system_content
            assert "topic: math" in system_content

    def test_build_dynamic_context_block(self):
        """Test building dynamic context block."""
        builder = DialogBuilder()
        dynamic_ctx = {
            "scenario": "discussion",
            "topic": "math",
            "question": "What is 2+2?",
            "is_new_question": True,
            "is_new_topic": False,
            "understanding_level": 5,
            "user_preferences": ["visual", "examples"],
        }

        result = builder._build_dynamic_context_block(dynamic_ctx)

        assert "Context:" in result
        assert "scenario: discussion" in result
        assert "topic: math" in result
        assert "question: What is 2+2?" in result
        assert "is_new_question: True" in result
        assert "is_new_topic: False" in result
        assert "understanding_level: 5" in result
        assert "user_preferences: visual, examples" in result

    def test_build_dynamic_context_block_with_none_values(self):
        """Test building dynamic context block with None values."""
        builder = DialogBuilder()
        dynamic_ctx = {
            "scenario": "discussion",
            "topic": None,
            "question": None,
            "is_new_question": False,
        }

        result = builder._build_dynamic_context_block(dynamic_ctx)

        assert "scenario: discussion" in result
        assert "is_new_question: False" in result
        # None values should not appear
        assert "topic: None" not in result
        assert "question: None" not in result

    def test_get_understanding_context_numeric_level(self):
        """Test getting understanding context with numeric level."""
        with patch("core.prompts.prompt_loader.PromptLoader") as mock_loader_class:
            mock_loader = MagicMock()
            mock_loader.get_system_prompt.return_value = None  # No custom prompt
            mock_loader_class.return_value = mock_loader

            builder = DialogBuilder()
            result = builder._get_understanding_context(2, mock_loader)

            assert "simple language" in result
            assert "examples" in result

    def test_get_understanding_context_string_level(self):
        """Test getting understanding context with string level."""
        with patch("core.prompts.prompt_loader.PromptLoader") as mock_loader_class:
            mock_loader = MagicMock()
            mock_loader.get_system_prompt.return_value = None  # No custom prompt
            mock_loader_class.return_value = mock_loader

            builder = DialogBuilder()
            result = builder._get_understanding_context("high", mock_loader)

            assert "detailed explanations" in result
            assert "related concepts" in result

    def test_build_topic_context(self):
        """Test building topic context."""
        builder = DialogBuilder()
        result = builder._build_topic_context("math")

        assert "Current topic: math" in result
        assert "Focus your explanations" in result

    def test_build_history_context(self, mock_session):
        """Test building history context."""
        builder = DialogBuilder()
        result = builder._build_history_context(mock_session)

        assert len(result) == 2
        assert result[0]["role"] == "user"
        assert result[0]["content"] == "Hello"
        assert result[1]["role"] == "assistant"  # bot role converted
        assert result[1]["content"] == "Hi there!"

    def test_get_fallback_base_prompt(self):
        """Test getting fallback base prompt."""
        builder = DialogBuilder()
        result = builder._get_fallback_base_prompt()

        assert "educational assistant" in result
        assert "children aged 7-11" in result
        assert "simple vocabulary" in result

    def test_handle_prompt_loading_failure(self):
        """Test handling prompt loading failure."""
        with patch("core.graceful_degradation.get_graceful_degradation_manager") as mock_degradation:
            mock_degradation_manager = MagicMock()
            mock_degradation_manager.handle_prompt_loading_failure.return_value = "Fallback prompt"
            mock_degradation.return_value = mock_degradation_manager

            builder = DialogBuilder()
            result = builder._handle_prompt_loading_failure("test_prompt")

            assert result == "Fallback prompt"
            mock_degradation_manager.handle_prompt_loading_failure.assert_called_once_with("test_prompt")
