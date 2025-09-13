"""Simple tests for persistence layer."""

import tempfile
from unittest.mock import patch

import pytest

from core.persistence.database import DatabaseManager, get_database_manager
from core.persistence.models import Message, Session
from core.persistence.session_adapter import PersistenceAdapter


class TestModels:
    """Test SQLAlchemy models."""

    def test_session_to_dict(self):
        """Test session to_dict method."""
        session = Session(
            chat_id="test_chat",
            scenario="discussion",
            topic="math",
            understanding_level=5,
        )

        data = session.to_dict()
        assert data["chat_id"] == "test_chat"
        assert data["scenario"] == "discussion"
        assert data["topic"] == "math"
        assert data["understanding_level"] == 5

    def test_session_from_dict(self):
        """Test session from_dict method."""
        data = {
            "chat_id": "test_chat",
            "scenario": "discussion",
            "topic": "math",
            "understanding_level": 5,
        }

        session = Session.from_dict(data)
        assert session.chat_id == "test_chat"
        assert session.scenario == "discussion"
        assert session.topic == "math"
        assert session.understanding_level == 5

    def test_message_to_dict(self):
        """Test message to_dict method."""
        message = Message(
            chat_id="test_chat",
            role="user",
            content="Hello",
        )

        data = message.to_dict()
        assert data["chat_id"] == "test_chat"
        assert data["role"] == "user"
        assert data["content"] == "Hello"

    def test_message_from_dict(self):
        """Test message from_dict method."""
        data = {
            "chat_id": "test_chat",
            "role": "user",
            "content": "Hello",
        }

        message = Message.from_dict(data)
        assert message.chat_id == "test_chat"
        assert message.role == "user"
        assert message.content == "Hello"


class TestDatabaseManager:
    """Test database manager functionality."""

    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database path."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            return f.name

    @pytest.fixture
    def db_manager(self, temp_db_path):
        """Create database manager with temporary database."""
        with patch("core.persistence.database.get_settings") as mock_settings:
            mock_settings.return_value.database_enabled = True
            mock_settings.return_value.database_path = temp_db_path
            manager = DatabaseManager()
            return manager

    @pytest.mark.asyncio
    async def test_database_initialization(self, db_manager):
        """Test database initialization."""
        await db_manager.initialize()
        assert db_manager.is_available
        await db_manager.close()

    @pytest.mark.asyncio
    async def test_database_disabled(self):
        """Test database manager when database is disabled."""
        with patch("core.persistence.database.get_settings") as mock_settings:
            mock_settings.return_value.database_enabled = False
            manager = DatabaseManager()
            await manager.initialize()
            assert not manager.is_available


class TestIntegration:
    """Integration tests for persistence layer."""

    @pytest.mark.asyncio
    async def test_graceful_degradation(self):
        """Test that the system works when database is disabled."""
        # This test ensures that when DATABASE_ENABLED=false,
        # the system falls back to in-memory storage gracefully

        with patch("core.persistence.database.get_settings") as mock_settings:
            mock_settings.return_value.database_enabled = False

            # All components should handle disabled database gracefully
            db_manager = get_database_manager()
            assert not db_manager.is_available

            adapter = PersistenceAdapter()
            assert not adapter.is_available

            # Operations should return safe defaults
            result = await adapter.load_session_state("test_chat")
            assert result is None

            result = await adapter.save_session_state({"chat_id": "test"})
            assert result is False
