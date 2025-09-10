"""Tests for prompt store functionality."""

from core.prompt_store import PromptStore
from core.session_state import SessionState


class TestPromptStore:
    """Test cases for PromptStore class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.prompt_store = PromptStore()
        self.session = SessionState(chat_id="test_chat_123")

    def test_prompt_store_initialization(self):
        """Test that prompt store initializes correctly."""
        assert self.prompt_store is not None
        assert hasattr(self.prompt_store, "_system_prompts")
        assert isinstance(self.prompt_store._system_prompts, dict)

    def test_load_system_prompts(self):
        """Test loading system prompts."""
        prompts = self.prompt_store._system_prompts

        # Should have at least the basic prompt
        assert "system_base" in prompts

        # Check that prompts are not empty
        assert len(prompts["system_base"]) > 0

    def test_build_context_basic(self):
        """Test basic context building."""
        user_message = "What is gravity?"
        messages = self.prompt_store.build_context(
            session=self.session,
            user_message=user_message,
            prompt_type="explanation",
        )

        # Should have system prompt and user message at minimum
        assert len(messages) >= 2

        # First message should be system
        assert messages[0]["role"] == "system"
        assert len(messages[0]["content"]) > 0

        # Last message should be user message
        assert messages[-1]["role"] == "user"
        assert messages[-1]["content"] == user_message

    def test_build_context_with_topic(self):
        """Test context building with active topic."""
        self.session.set_topic("science")
        user_message = "Tell me about atoms"

        messages = self.prompt_store.build_context(
            session=self.session,
            user_message=user_message,
            prompt_type="explanation",
        )

        # Should have system prompt, topic context, and user message
        assert len(messages) >= 3

        # Check for topic context in system messages
        system_messages = [msg for msg in messages if msg["role"] == "system"]
        topic_found = any("science" in msg["content"] for msg in system_messages)
        assert topic_found

    def test_build_context_with_history(self):
        """Test context building with conversation history."""
        # Add some history
        self.session.add_message("user", "What is water?")
        self.session.add_message("bot", "Water is a liquid that we drink.")
        self.session.add_message("user", "Where does it come from?")

        user_message = "Is it safe to drink?"
        messages = self.prompt_store.build_context(
            session=self.session,
            user_message=user_message,
            prompt_type="question",
        )

        # Should have system prompt, history, and current message
        assert len(messages) >= 5  # system + 3 history + current

        # Check that history is included
        user_messages = [msg for msg in messages if msg["role"] == "user"]
        assert len(user_messages) >= 3  # 2 from history + 1 current

        # Check that assistant (converted bot) message is included
        assistant_messages = [msg for msg in messages if msg["role"] == "assistant"]
        assert len(assistant_messages) >= 1

    def test_get_understanding_context(self):
        """Test understanding level context generation."""
        # Test all levels
        for level in ["low", "medium", "high"]:
            context = self.prompt_store._get_understanding_context(level)
            assert isinstance(context, str)
            assert len(context) > 0

        # Test invalid level (should return medium)
        context = self.prompt_store._get_understanding_context("invalid")
        assert isinstance(context, str)
        assert len(context) > 0

    def test_build_topic_context(self):
        """Test topic context building."""
        topic = "mathematics"
        context = self.prompt_store._build_topic_context(topic)

        assert isinstance(context, str)
        assert len(context) > 0
        assert topic in context

    def test_get_available_topics(self):
        """Test getting available topics."""
        topics = self.prompt_store.get_available_topics()

        assert isinstance(topics, list)
        assert len(topics) > 0

        # Check for some expected topics
        expected_topics = ["math", "science", "reading", "writing"]
        for topic in expected_topics:
            assert topic in topics

    def test_validate_topic(self):
        """Test topic validation."""
        # Valid topics
        assert self.prompt_store.validate_topic("math")
        assert self.prompt_store.validate_topic("MATH")  # Case insensitive
        assert self.prompt_store.validate_topic("science")

        # Invalid topics
        assert not self.prompt_store.validate_topic("invalid_topic")
        assert not self.prompt_store.validate_topic("")
        assert not self.prompt_store.validate_topic("   ")

    def test_prompt_type_handling(self):
        """Test different prompt types."""
        user_message = "Hello"

        # Test explanation type
        messages_explanation = self.prompt_store.build_context(
            session=self.session,
            user_message=user_message,
            prompt_type="explanation",
        )

        # Test question type
        messages_question = self.prompt_store.build_context(
            session=self.session,
            user_message=user_message,
            prompt_type="question",
        )

        # Test invalid type (should default to explanation)
        messages_invalid = self.prompt_store.build_context(
            session=self.session,
            user_message=user_message,
            prompt_type="invalid",
        )

        # All should return valid messages
        assert len(messages_explanation) >= 2
        assert len(messages_question) >= 2
        assert len(messages_invalid) >= 2

    def test_history_limit(self):
        """Test that history is limited correctly."""
        # Add many messages to exceed limit
        for i in range(50):
            self.session.add_message("user", f"Message {i}")
            self.session.add_message("bot", f"Response {i}")

        user_message = "Final message"
        messages = self.prompt_store.build_context(
            session=self.session,
            user_message=user_message,
            prompt_type="explanation",
        )

        # Should not have all 100 messages (50 user + 50 bot)
        # Should be limited to recent messages
        user_messages = [msg for msg in messages if msg["role"] == "user"]
        bot_messages = [msg for msg in messages if msg["role"] == "bot"]

        # Should have reasonable number of messages (not all 50)
        assert len(user_messages) < 50
        assert len(bot_messages) < 50

        # Should still have the final message
        assert messages[-1]["content"] == user_message


class TestPromptStoreIntegration:
    """Integration tests for PromptStore with SessionState."""

    def test_full_workflow(self):
        """Test complete workflow from session to context."""
        # Create session with topic and history
        session = SessionState(chat_id="integration_test")
        session.set_topic("science")
        session.update_understanding_level("medium")
        session.add_message("user", "What is photosynthesis?")
        session.add_message(
            "bot", "Photosynthesis is how plants make food using sunlight."
        )

        # Build context
        prompt_store = PromptStore()
        messages = prompt_store.build_context(
            session=session,
            user_message="Can you explain more?",
            prompt_type="explanation",
        )

        # Verify context structure
        assert len(messages) >= 4  # system + topic + history + current

        # Check system message
        system_msg = messages[0]
        assert system_msg["role"] == "system"
        assert "science" in system_msg["content"] or any(
            "science" in msg["content"] for msg in messages if msg["role"] == "system"
        )

        # Check history preservation
        user_messages = [msg for msg in messages if msg["role"] == "user"]
        assert len(user_messages) >= 2  # history + current

        # Check current message
        assert messages[-1]["role"] == "user"
        assert messages[-1]["content"] == "Can you explain more?"
