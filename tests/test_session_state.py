"""Tests for session state management."""

from datetime import datetime, timedelta

import pytest

from core.session_state import (
    Message,
    SessionManager,
    SessionState,
    get_session_manager,
)


class TestMessage:
    """Test cases for Message class."""

    def test_message_creation(self):
        """Test message creation with role and content."""
        message = Message("user", "Hello, world!")

        assert message.role == "user"
        assert message.content == "Hello, world!"
        assert isinstance(message.timestamp, datetime)

    def test_message_timestamp(self):
        """Test that message timestamp is set correctly."""
        before = datetime.now()
        message = Message("assistant", "Hi there!")
        after = datetime.now()

        assert before <= message.timestamp <= after


class TestSessionState:
    """Test cases for SessionState class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.session = SessionState(chat_id="test_chat_123")

    def test_session_initialization(self):
        """Test session initialization with default values."""
        assert self.session.chat_id == "test_chat_123"
        assert self.session.scenario == "unknown"
        assert self.session.question is None
        assert self.session.topic is None
        assert self.session.is_new_question is False
        assert self.session.is_new_topic is False
        assert self.session.understanding_level == 5
        assert self.session.previous_understanding_level is None
        assert self.session.previous_topic is None
        assert self.session.user_preferences == []
        assert self.session.recent_messages == []
        assert isinstance(self.session.updated_at, datetime)

    def test_add_message(self):
        """Test adding messages to session."""
        self.session.add_message("user", "Hello!")
        self.session.add_message("assistant", "Hi there!")

        assert len(self.session.recent_messages) == 2
        assert self.session.recent_messages[0].role == "user"
        assert self.session.recent_messages[0].content == "Hello!"
        assert self.session.recent_messages[1].role == "assistant"
        assert self.session.recent_messages[1].content == "Hi there!"

    def test_get_recent_messages_with_limit(self):
        """Test getting recent messages with limit."""
        # Add 5 messages
        for i in range(5):
            self.session.add_message("user", f"Message {i}")

        # Get last 3 messages
        recent = self.session.get_recent_messages(limit=3)

        assert len(recent) == 3
        assert recent[0].content == "Message 2"
        assert recent[1].content == "Message 3"
        assert recent[2].content == "Message 4"

    def test_get_recent_messages_default_limit(self):
        """Test getting recent messages with default limit."""
        # Add 35 messages (more than default limit of 30)
        for i in range(35):
            self.session.add_message("user", f"Message {i}")

        recent = self.session.get_recent_messages()

        assert len(recent) == 30  # Default limit
        assert recent[0].content == "Message 5"  # First 5 messages should be excluded
        assert recent[-1].content == "Message 34"  # Last message

    def test_set_topic_new_topic(self):
        """Test setting a new topic."""
        self.session.set_topic("mathematics")

        assert self.session.topic == "mathematics"
        assert self.session.is_new_topic is True
        assert self.session.scenario == "discussion"
        assert self.session.question is None  # Should be reset
        assert self.session.previous_topic is None  # No previous topic

    def test_set_topic_change_topic(self):
        """Test changing from one topic to another."""
        # Set initial topic
        self.session.set_topic("mathematics")
        self.session.is_new_topic = False  # Reset flag

        # Change to new topic
        self.session.set_topic("science")

        assert self.session.topic == "science"
        assert self.session.is_new_topic is True
        assert self.session.previous_topic == "mathematics"
        assert self.session.question is None  # Should be reset

    def test_update_understanding_level_numeric(self):
        """Test updating understanding level with numeric value."""
        self.session.update_understanding_level(7)

        assert self.session.understanding_level == 7
        assert self.session.previous_understanding_level == 5  # Original value

    def test_update_understanding_level_string_low(self):
        """Test updating understanding level with string 'low'."""
        self.session.update_understanding_level("low")

        assert self.session.understanding_level == 2
        assert self.session.previous_understanding_level == 5

    def test_update_understanding_level_string_medium(self):
        """Test updating understanding level with string 'medium'."""
        self.session.update_understanding_level("medium")

        assert self.session.understanding_level == 5
        assert self.session.previous_understanding_level == 5

    def test_update_understanding_level_string_high(self):
        """Test updating understanding level with string 'high'."""
        self.session.update_understanding_level("high")

        assert self.session.understanding_level == 8
        assert self.session.previous_understanding_level == 5

    def test_update_understanding_level_invalid_string(self):
        """Test updating understanding level with invalid string."""
        original_level = self.session.understanding_level
        self.session.update_understanding_level("invalid")

        # Should keep original level
        assert self.session.understanding_level == original_level

    def test_update_understanding_level_out_of_range(self):
        """Test updating understanding level with out-of-range value."""
        original_level = self.session.understanding_level

        # Test negative value
        self.session.update_understanding_level(-1)
        assert self.session.understanding_level == original_level

        # Test value > 9
        self.session.update_understanding_level(10)
        assert self.session.understanding_level == original_level

    def test_active_topic_property(self):
        """Test active_topic property for backward compatibility."""
        self.session.topic = "test_topic"
        assert self.session.active_topic == "test_topic"

    def test_reset_session(self):
        """Test session reset functionality."""
        # Set up session with data
        self.session.set_topic("mathematics")
        self.session.add_message("user", "Hello")
        self.session.update_understanding_level(8)

        # Reset session
        self.session.reset_session()

        assert self.session.topic is None
        assert self.session.understanding_level == 5  # Reset to default medium level
        assert len(self.session.recent_messages) == 0


class TestSessionManager:
    """Test cases for SessionManager class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = SessionManager()

    @pytest.mark.asyncio
    async def test_get_session_new_session(self):
        """Test getting a new session."""
        session = await self.manager.get_session("new_chat_123")

        assert isinstance(session, SessionState)
        assert session.chat_id == "new_chat_123"
        assert "new_chat_123" in self.manager._sessions

    @pytest.mark.asyncio
    async def test_get_session_existing_session(self):
        """Test getting an existing session."""
        # Create session first
        session1 = await self.manager.get_session("existing_chat")

        # Get same session again
        session2 = await self.manager.get_session("existing_chat")

        assert session1 is session2  # Same object
        assert len(self.manager._sessions) == 1

    @pytest.mark.asyncio
    async def test_remove_session(self):
        """Test removing a session."""
        # Create session
        await self.manager.get_session("to_remove")
        assert "to_remove" in self.manager._sessions

        # Remove session
        self.manager.remove_session("to_remove")
        assert "to_remove" not in self.manager._sessions

    def test_remove_nonexistent_session(self):
        """Test removing a session that doesn't exist."""
        # Should not raise an error
        self.manager.remove_session("nonexistent")
        assert "nonexistent" not in self.manager._sessions

    @pytest.mark.asyncio
    async def test_get_all_sessions(self):
        """Test getting all sessions."""
        # Create multiple sessions
        session1 = await self.manager.get_session("chat1")
        session2 = await self.manager.get_session("chat2")

        all_sessions = self.manager.get_all_sessions()

        assert len(all_sessions) == 2
        assert "chat1" in all_sessions
        assert "chat2" in all_sessions
        assert all_sessions["chat1"] is session1
        assert all_sessions["chat2"] is session2

    @pytest.mark.asyncio
    async def test_cleanup_old_sessions(self):
        """Test cleaning up old sessions."""
        # Create a session
        session = await self.manager.get_session("old_chat")

        # Manually set old timestamp
        session.updated_at = datetime.now() - timedelta(hours=25)

        # Cleanup sessions older than 24 hours
        removed_count = self.manager.cleanup_old_sessions(max_age_hours=24)

        assert removed_count == 1
        assert "old_chat" not in self.manager._sessions

    @pytest.mark.asyncio
    async def test_cleanup_old_sessions_none_to_remove(self):
        """Test cleanup when no sessions need removal."""
        # Create a recent session
        await self.manager.get_session("recent_chat")

        # Cleanup sessions older than 24 hours
        removed_count = self.manager.cleanup_old_sessions(max_age_hours=24)

        assert removed_count == 0
        assert "recent_chat" in self.manager._sessions

    @pytest.mark.asyncio
    async def test_cleanup_old_sessions_custom_age(self):
        """Test cleanup with custom age limit."""
        # Create a session
        session = await self.manager.get_session("custom_age_chat")

        # Set timestamp to 2 hours ago
        session.updated_at = datetime.now() - timedelta(hours=2)

        # Cleanup sessions older than 1 hour
        removed_count = self.manager.cleanup_old_sessions(max_age_hours=1)

        assert removed_count == 1
        assert "custom_age_chat" not in self.manager._sessions


class TestGlobalSessionManager:
    """Test cases for global session manager."""

    def test_get_session_manager_singleton(self):
        """Test that get_session_manager returns singleton."""
        manager1 = get_session_manager()
        manager2 = get_session_manager()

        assert manager1 is manager2
        assert isinstance(manager1, SessionManager)

    @pytest.mark.asyncio
    async def test_global_session_manager_functionality(self):
        """Test that global session manager works correctly."""
        manager = get_session_manager()

        # Create session through global manager
        session = await manager.get_session("global_test")

        assert isinstance(session, SessionState)
        assert session.chat_id == "global_test"
