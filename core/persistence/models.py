"""SQLAlchemy models for the bot database."""

from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(AsyncAttrs, DeclarativeBase):
    """Base class for all models."""


class Session(Base):
    """Session model for storing chat sessions."""

    __tablename__ = "sessions"

    chat_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    scenario: Mapped[str] = mapped_column(String(50), nullable=False, default="unknown")
    question: Mapped[str | None] = mapped_column(Text, nullable=True)
    topic: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_new_question: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    is_new_topic: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    understanding_level: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )  # 0-9 scale
    previous_understanding_level: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    previous_topic: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_preferences: Mapped[str] = mapped_column(
        Text, nullable=False, default="[]"
    )  # JSON array
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now(), onupdate=func.now()
    )

    # Relationship to messages
    messages: Mapped[list["Message"]] = relationship(
        "Message", back_populates="session", cascade="all, delete-orphan"
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert session to dictionary."""
        return {
            "chat_id": self.chat_id,
            "scenario": self.scenario,
            "question": self.question,
            "topic": self.topic,
            "is_new_question": self.is_new_question,
            "is_new_topic": self.is_new_topic,
            "understanding_level": self.understanding_level,
            "previous_understanding_level": self.previous_understanding_level,
            "previous_topic": self.previous_topic,
            "user_preferences": self.user_preferences,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Session":
        """Create session from dictionary."""
        return cls(**data)


class Message(Base):
    """Message model for storing chat messages."""

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chat_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("sessions.chat_id"), nullable=False
    )
    role: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # "user" or "assistant"
    content: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now()
    )

    # Relationship to session
    session: Mapped["Session"] = relationship("Session", back_populates="messages")

    def to_dict(self) -> dict[str, Any]:
        """Convert message to dictionary."""
        return {
            "id": self.id,
            "chat_id": self.chat_id,
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Message":
        """Create message from dictionary."""
        return cls(**data)


class Migration(Base):
    """Migration model for tracking applied migrations."""

    __tablename__ = "migrations"

    version: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    applied_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now()
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert migration to dictionary."""
        return {
            "version": self.version,
            "name": self.name,
            "applied_at": self.applied_at,
        }
