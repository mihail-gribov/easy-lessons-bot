"""Adapter for integrating persistence layer with existing session management."""

import json
import logging
from typing import Any

from core.persistence.database import get_database_manager
from core.persistence.repositories import get_message_repository, get_session_repository

logger = logging.getLogger(__name__)


class PersistenceAdapter:
    """Adapter for integrating persistence with SessionManager."""

    def __init__(self) -> None:
        """Initialize persistence adapter."""
        self.db_manager = get_database_manager()
        self.session_repo = get_session_repository()
        self.message_repo = get_message_repository()

    async def load_session_state(self, chat_id: str) -> dict[str, Any] | None:
        """Load session state from database."""
        if not self.db_manager.is_available:
            logger.debug("Database not available, returning None for %s", chat_id)
            return None

        try:
            session = await self.session_repo.get_session(chat_id)
            if not session:
                logger.debug("No session found for %s", chat_id)
                return None

            # Load recent messages
            messages = await self.message_repo.get_messages(chat_id, limit=30)

            # Convert to session state format
            session_state = {
                "chat_id": session.chat_id,
                "scenario": session.scenario,
                "question": session.question,
                "topic": session.topic,
                "is_new_question": session.is_new_question,
                "is_new_topic": session.is_new_topic,
                "understanding_level": session.understanding_level,
                "previous_understanding_level": session.previous_understanding_level,
                "previous_topic": session.previous_topic,
                "user_preferences": json.loads(session.user_preferences),
                "messages": messages,
                "created_at": session.created_at.isoformat()
                if session.created_at
                else None,
                "updated_at": session.updated_at.isoformat()
                if session.updated_at
                else None,
            }

            logger.debug("Loaded session state for %s", chat_id)
            return session_state

        except Exception:
            logger.exception("Failed to load session state for %s", chat_id)
            return None

    async def save_session_state(self, session_state: dict[str, Any]) -> bool:
        """Save session state to database."""
        if not self.db_manager.is_available:
            logger.debug("Database not available, skipping save")
            return False

        try:
            chat_id = session_state["chat_id"]

            # Prepare session data
            session_data = {
                "chat_id": chat_id,
                "scenario": session_state.get("scenario", "unknown"),
                "question": session_state.get("question"),
                "topic": session_state.get("topic"),
                "is_new_question": session_state.get("is_new_question", False),
                "is_new_topic": session_state.get("is_new_topic", False),
                "understanding_level": session_state.get("understanding_level", 0),
                "previous_understanding_level": session_state.get(
                    "previous_understanding_level"
                ),
                "previous_topic": session_state.get("previous_topic"),
                "user_preferences": json.dumps(
                    session_state.get("user_preferences", [])
                ),
            }

            # Save session
            success = await self.session_repo.save_session(session_data)
            if not success:
                logger.error("Failed to save session for %s", chat_id)
                return False

            # Save new messages (only the latest ones that aren't already saved)
            messages = session_state.get("messages", [])
            if messages:
                # Get existing message count to determine which messages are new
                existing_count = await self.message_repo.get_message_count(chat_id)

                # Save only new messages (assuming messages are ordered chronologically)
                new_messages = messages[existing_count:]
                for message in new_messages:
                    await self.message_repo.add_message(
                        chat_id=chat_id,
                        role=message["role"],
                        content=message["content"],
                    )

            logger.debug("Saved session state for %s", chat_id)
            return True

        except Exception:
            logger.exception("Failed to save session state")
            return False

    async def add_message(self, chat_id: str, role: str, content: str) -> bool:
        """Add a single message to the database."""
        if not self.db_manager.is_available:
            return False

        try:
            return await self.message_repo.add_message(chat_id, role, content)
        except Exception:
            logger.exception("Failed to add message for %s", chat_id)
            return False

    async def get_messages(self, chat_id: str, limit: int = 30) -> list[dict[str, Any]]:
        """Get messages for a session."""
        if not self.db_manager.is_available:
            return []

        try:
            return await self.message_repo.get_messages(chat_id, limit)
        except Exception:
            logger.exception("Failed to get messages for %s", chat_id)
            return []

    async def delete_session(self, chat_id: str) -> bool:
        """Delete session and all its messages."""
        if not self.db_manager.is_available:
            return False

        try:
            return await self.session_repo.delete_session(chat_id)
        except Exception:
            logger.exception("Failed to delete session %s", chat_id)
            return False

    async def cleanup_old_sessions(self, hours: int = 168) -> int:
        """Clean up old sessions."""
        if not self.db_manager.is_available:
            return 0

        try:
            return await self.session_repo.cleanup_old_sessions(hours)
        except Exception:
            logger.exception("Failed to cleanup old sessions")
            return 0

    @property
    def is_available(self) -> bool:
        """Check if persistence is available."""
        return self.db_manager.is_available


# Global persistence adapter instance
_persistence_adapter: PersistenceAdapter | None = None


def get_persistence_adapter() -> PersistenceAdapter:
    """Get global persistence adapter instance."""
    global _persistence_adapter  # noqa: PLW0603
    if _persistence_adapter is None:
        _persistence_adapter = PersistenceAdapter()
    return _persistence_adapter
