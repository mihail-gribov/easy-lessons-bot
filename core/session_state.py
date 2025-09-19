"""Session state management with persistence support."""

import logging
from datetime import datetime, timedelta

from core.persistence.session_adapter import get_persistence_adapter

logger = logging.getLogger(__name__)


class Message:
    """Represents a single message in conversation history."""

    def __init__(self, role: str, content: str) -> None:
        """
        Initialize message.

        Args:
            role: Message role ('user' or 'assistant')
            content: Message content
        """
        self.role = role
        self.content = content
        self.timestamp = datetime.now()


class SessionState:
    """In-memory session state for a user with dynamic dialog context."""

    def __init__(self, chat_id: str | int) -> None:
        """
        Initialize session state.

        Args:
            chat_id: Telegram chat ID
        """
        self.chat_id = chat_id

        # Dynamic dialog context (iteration 8)
        self.scenario: str = "unknown"
        self.question: str | None = None
        self.topic: str | None = None
        self.is_new_question: bool = False
        self.is_new_topic: bool = False
        self.understanding_level: int = 5  # 0..9 scale
        self.previous_understanding_level: int | None = None
        self.previous_topic: str | None = None
        self.user_preferences: list[str] = []

        # Image analysis fields
        self.last_image_analysis: str | None = None
        self.image_analysis_count: int = 0

        # Conversation history
        self.recent_messages: list[Message] = []
        self.updated_at = datetime.now()

    def add_message(self, role: str, content: str) -> None:
        """
        Add message to conversation history.

        Args:
            role: Message role ('user' or 'assistant')
            content: Message content
        """
        message = Message(role, content)
        self.recent_messages.append(message)
        self.updated_at = datetime.now()

        logger.debug(
            "Added message to session %s: role=%s, content_length=%d",
            self.chat_id,
            role,
            len(content),
        )

    def to_dict(self) -> dict:
        """Convert session state to dictionary for persistence."""
        return {
            "chat_id": str(self.chat_id),
            "scenario": self.scenario,
            "question": self.question,
            "topic": self.topic,
            "is_new_question": self.is_new_question,
            "is_new_topic": self.is_new_topic,
            "understanding_level": self.understanding_level,
            "previous_understanding_level": self.previous_understanding_level,
            "previous_topic": self.previous_topic,
            "user_preferences": self.user_preferences,
            "last_image_analysis": self.last_image_analysis,
            "image_analysis_count": self.image_analysis_count,
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                }
                for msg in self.recent_messages
            ],
            "created_at": self.updated_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SessionState":
        """Create session state from dictionary."""
        session = cls(data["chat_id"])
        session.scenario = data.get("scenario", "unknown")
        session.question = data.get("question")
        session.topic = data.get("topic")
        session.is_new_question = data.get("is_new_question", False)
        session.is_new_topic = data.get("is_new_topic", False)
        session.understanding_level = data.get("understanding_level", 5)
        session.previous_understanding_level = data.get("previous_understanding_level")
        session.previous_topic = data.get("previous_topic")
        session.user_preferences = data.get("user_preferences", [])
        session.last_image_analysis = data.get("last_image_analysis")
        session.image_analysis_count = data.get("image_analysis_count", 0)

        # Restore messages
        messages_data = data.get("messages", [])
        for msg_data in messages_data:
            message = Message(msg_data["role"], msg_data["content"])
            if "timestamp" in msg_data:
                message.timestamp = datetime.fromisoformat(msg_data["timestamp"])
            session.recent_messages.append(message)

        return session

    def get_recent_messages(self, limit: int = 30) -> list[Message]:
        """
        Get recent messages with limit.

        Args:
            limit: Maximum number of messages to return

        Returns:
            List of recent messages
        """
        return self.recent_messages[-limit:]

    def set_topic(self, topic: str) -> None:
        """Set current topic and update related dynamic context."""
        # Track previous topic
        if self.topic and self.topic != topic:
            self.previous_topic = self.topic

        self.topic = topic
        self.is_new_topic = True
        self.scenario = "discussion"

        # Reset question when switching the topic
        self.question = None

        # Reset understanding progression for new topic
        self.previous_understanding_level = self.understanding_level
        self.understanding_level = 5

        self.updated_at = datetime.now()

        logger.info("Set topic for session %s: %s", self.chat_id, topic)

    def update_understanding_level(self, level: int | str) -> None:
        """Update understanding level (accepts 0..9 or legacy labels)."""
        self.previous_understanding_level = self.understanding_level

        # Support legacy labels for backward compatibility
        if isinstance(level, str):
            label = level.lower()
            if label == "low":
                numeric = 2
            elif label == "medium":
                numeric = 5
            elif label == "high":
                numeric = 8
            else:
                logger.warning(
                    "Invalid understanding level label: %s, keeping current: %s",
                    level,
                    self.understanding_level,
                )
                return
        else:
            numeric = int(level)

        if numeric < 0 or numeric > 9:
            logger.warning(
                "Invalid understanding level value: %s, keeping current: %s",
                level,
                self.understanding_level,
            )
            return

        self.understanding_level = numeric
        self.updated_at = datetime.now()

        logger.debug(
            "Updated understanding level for session %s: %d",
            self.chat_id,
            numeric,
        )

    # Compatibility helpers for legacy access patterns
    @property
    def active_topic(self) -> str | None:
        """Back-compat property alias for current topic."""
        return self.topic

    def reset_session(self) -> None:
        """Reset session state."""
        self.topic = None
        self.understanding_level = 5  # Reset to default medium level
        self.recent_messages.clear()
        self.updated_at = datetime.now()

        logger.info("Reset session state for chat %s", self.chat_id)


class SessionManager:
    """Manages session states with persistence support."""

    def __init__(self) -> None:
        """Initialize session manager."""
        self._sessions: dict[str | int, SessionState] = {}
        self._persistence_adapter = get_persistence_adapter()

    async def get_session(self, chat_id: str | int) -> SessionState:
        """
        Get or create session for chat with persistence support.

        Args:
            chat_id: Telegram chat ID

        Returns:
            Session state
        """
        chat_id_str = str(chat_id)

        # Try to load from persistence first
        if chat_id_str not in self._sessions and self._persistence_adapter.is_available:
            try:
                session_data = await self._persistence_adapter.load_session_state(
                    chat_id_str
                )
                if session_data:
                    self._sessions[chat_id_str] = SessionState.from_dict(session_data)
                    logger.info("Loaded session from persistence for chat %s", chat_id)
                    return self._sessions[chat_id_str]
            except Exception as e:  # noqa: BLE001
                logger.warning(
                    "Failed to load session from persistence for %s: %s", chat_id, e
                )

        # Create new session if not found
        if chat_id_str not in self._sessions:
            self._sessions[chat_id_str] = SessionState(chat_id)
            logger.info("Created new session for chat %s", chat_id)

        return self._sessions[chat_id_str]

    async def save_session(self, session: SessionState) -> None:
        """
        Save session to persistence.

        Args:
            session: Session state to save
        """
        if self._persistence_adapter.is_available:
            try:
                session_data = session.to_dict()
                await self._persistence_adapter.save_session_state(session_data)
                logger.debug(
                    "Saved session to persistence for chat %s", session.chat_id
                )
            except Exception as e:  # noqa: BLE001
                logger.warning(
                    "Failed to save session to persistence for %s: %s",
                    session.chat_id,
                    e,
                )

    def remove_session(self, chat_id: str | int) -> None:
        """
        Remove session from memory.

        Args:
            chat_id: Telegram chat ID
        """
        if chat_id in self._sessions:
            del self._sessions[chat_id]
            logger.info("Removed session for chat %s", chat_id)

    def get_all_sessions(self) -> dict[str | int, SessionState]:
        """
        Get all active sessions.

        Returns:
            Dictionary of all sessions
        """
        return self._sessions.copy()

    def cleanup_old_sessions(self, max_age_hours: int = 24) -> int:
        """
        Remove sessions older than specified hours.

        Args:
            max_age_hours: Maximum age in hours

        Returns:
            Number of sessions removed
        """
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        sessions_to_remove = []

        for chat_id, session in self._sessions.items():
            if session.updated_at < cutoff_time:
                sessions_to_remove.append(chat_id)

        for chat_id in sessions_to_remove:
            del self._sessions[chat_id]

        if sessions_to_remove:
            logger.info(
                "Cleaned up %d old sessions (older than %d hours)",
                len(sessions_to_remove),
                max_age_hours,
            )

        return len(sessions_to_remove)


# Global session manager instance
_session_manager: SessionManager | None = None


def get_session_manager() -> SessionManager:
    """Get global session manager instance."""
    global _session_manager  # noqa: PLW0603
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager
