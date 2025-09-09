"""Session state management for in-memory user sessions."""

import logging
from datetime import datetime, timedelta

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
        self.active_topic = None
        self.understanding_level = "medium"
        self.recent_messages.clear()
        self.updated_at = datetime.now()

        logger.info("Reset session state for chat %s", self.chat_id)


class SessionManager:
    """Manages in-memory session states."""

    def __init__(self) -> None:
        """Initialize session manager."""
        self._sessions: dict[str | int, SessionState] = {}

    def get_session(self, chat_id: str | int) -> SessionState:
        """
        Get or create session for chat.

        Args:
            chat_id: Telegram chat ID

        Returns:
            Session state
        """
        if chat_id not in self._sessions:
            self._sessions[chat_id] = SessionState(chat_id)
            logger.info("Created new session for chat %s", chat_id)

        return self._sessions[chat_id]

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
