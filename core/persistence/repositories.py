"""Repository layer for database operations."""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import desc, select

from core.persistence.database import get_database_manager
from core.persistence.models import Message, Session

logger = logging.getLogger(__name__)


class SessionRepository:
    """Repository for session operations."""

    def __init__(self) -> None:
        """Initialize session repository."""
        self.db_manager = get_database_manager()

    async def get_session(self, chat_id: str) -> Session | None:
        """Get session by chat_id."""
        if not self.db_manager.is_available:
            return None

        try:
            async with self.db_manager.get_session() as session:
                result = await session.execute(
                    select(Session).where(Session.chat_id == chat_id)
                )
                return result.scalar_one_or_none()

        except Exception:
            logger.exception("Failed to get session %s", chat_id)
            return None

    async def save_session(self, session_data: dict[str, Any]) -> bool:
        """Save or update session."""
        if not self.db_manager.is_available:
            return False

        try:
            async with self.db_manager.get_session() as session:
                # Check if session exists
                existing = await session.execute(
                    select(Session).where(Session.chat_id == session_data["chat_id"])
                )
                existing_session = existing.scalar_one_or_none()

                if existing_session:
                    # Update existing session
                    for key, value in session_data.items():
                        if key != "chat_id" and hasattr(existing_session, key):
                            setattr(existing_session, key, value)
                    existing_session.updated_at = datetime.now(UTC)
                else:
                    # Create new session
                    new_session = Session.from_dict(session_data)
                    session.add(new_session)

                await session.commit()
                return True

        except Exception:
            logger.exception("Failed to save session %s", session_data.get("chat_id"))
            return False

    async def delete_session(self, chat_id: str) -> bool:
        """Delete session and all its messages."""
        if not self.db_manager.is_available:
            return False

        try:
            async with self.db_manager.get_session() as session:
                result = await session.execute(
                    select(Session).where(Session.chat_id == chat_id)
                )
                session_obj = result.scalar_one_or_none()

                if session_obj:
                    await session.delete(session_obj)
                    await session.commit()
                    return True

                return False

        except Exception:
            logger.exception("Failed to delete session %s", chat_id)
            return False

    async def cleanup_old_sessions(self, hours: int = 168) -> int:
        """Clean up sessions older than specified hours."""
        if not self.db_manager.is_available:
            return 0

        try:
            cutoff_time = datetime.now(UTC) - timedelta(hours=hours)
            deleted_count = 0

            async with self.db_manager.get_session() as session:
                # Get old sessions
                result = await session.execute(
                    select(Session).where(Session.updated_at < cutoff_time)
                )
                old_sessions = result.scalars().all()

                # Delete old sessions (cascade will delete messages)
                for session_obj in old_sessions:
                    await session.delete(session_obj)
                    deleted_count += 1

                await session.commit()
                logger.info("Cleaned up %d old sessions", deleted_count)
                return deleted_count

        except Exception:
            logger.exception("Failed to cleanup old sessions")
            return 0


class MessageRepository:
    """Repository for message operations."""

    def __init__(self) -> None:
        """Initialize message repository."""
        self.db_manager = get_database_manager()

    async def add_message(self, chat_id: str, role: str, content: str) -> bool:
        """Add message to session."""
        if not self.db_manager.is_available:
            return False

        try:
            async with self.db_manager.get_session() as session:
                message = Message(
                    chat_id=chat_id,
                    role=role,
                    content=content,
                    timestamp=datetime.now(UTC),
                )
                session.add(message)
                await session.commit()
                return True

        except Exception:
            logger.exception("Failed to add message for %s", chat_id)
            return False

    async def get_messages(self, chat_id: str, limit: int = 30) -> list[dict[str, Any]]:
        """Get recent messages for session."""
        if not self.db_manager.is_available:
            return []

        try:
            async with self.db_manager.get_session() as session:
                result = await session.execute(
                    select(Message)
                    .where(Message.chat_id == chat_id)
                    .order_by(desc(Message.timestamp))
                    .limit(limit)
                )
                messages = result.scalars().all()

                # Convert to list of dicts and reverse order (oldest first)
                return [msg.to_dict() for msg in reversed(messages)]

        except Exception:
            logger.exception("Failed to get messages for %s", chat_id)
            return []

    async def get_message_count(self, chat_id: str) -> int:
        """Get total message count for session."""
        if not self.db_manager.is_available:
            return 0

        try:
            async with self.db_manager.get_session() as session:
                result = await session.execute(
                    select(Message).where(Message.chat_id == chat_id)
                )
                return len(result.scalars().all())

        except Exception:
            logger.exception("Failed to get message count for %s", chat_id)
            return 0

    async def delete_messages(self, chat_id: str) -> bool:
        """Delete all messages for session."""
        if not self.db_manager.is_available:
            return False

        try:
            async with self.db_manager.get_session() as session:
                await session.execute(select(Message).where(Message.chat_id == chat_id))
                result = await session.execute(
                    select(Message).where(Message.chat_id == chat_id)
                )
                messages = result.scalars().all()

                for message in messages:
                    await session.delete(message)

                await session.commit()
                return True

        except Exception:
            logger.exception("Failed to delete messages for %s", chat_id)
            return False


# Global repository instances
_session_repo: SessionRepository | None = None
_message_repo: MessageRepository | None = None


def get_session_repository() -> SessionRepository:
    """Get global session repository instance."""
    global _session_repo  # noqa: PLW0603
    if _session_repo is None:
        _session_repo = SessionRepository()
    return _session_repo


def get_message_repository() -> MessageRepository:
    """Get global message repository instance."""
    global _message_repo  # noqa: PLW0603
    if _message_repo is None:
        _message_repo = MessageRepository()
    return _message_repo
