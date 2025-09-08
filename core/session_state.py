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
            role: Message role ('user' or 'bot')
            content: Message content
        """
        self.role = role
        self.content = content
        self.timestamp = datetime.now()


class SessionState:
    """In-memory session state for a user."""

    def __init__(self, chat_id: str | int) -> None:
        """
        Initialize session state.

        Args:
            chat_id: Telegram chat ID
        """
        self.chat_id = chat_id
        self.active_topic: str | None = None
        self.understanding_level: str = "medium"  # low, medium, high
        self.recent_messages: list[Message] = []
        self.updated_at = datetime.now()

    def add_message(self, role: str, content: str) -> None:
        """
        Add message to conversation history.

        Args:
            role: Message role ('user' or 'bot')
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
        """
        Set active topic and reset understanding level.

        Args:
            topic: Topic name
        """
        self.active_topic = topic
        self.understanding_level = "medium"  # Reset to medium for new topic
        self.updated_at = datetime.now()

        logger.info("Set topic for session %s: %s", self.chat_id, topic)

    def update_understanding_level(self, level: str) -> None:
        """
        Update understanding level.

        Args:
            level: Understanding level ('low', 'medium', 'high')
        """
        if level not in ["low", "medium", "high"]:
            logger.warning(
                "Invalid understanding level: %s, keeping current: %s",
                level,
                self.understanding_level,
            )
            return

        self.understanding_level = level
        self.updated_at = datetime.now()

        logger.debug(
            "Updated understanding level for session %s: %s",
            self.chat_id,
            level,
        )

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
