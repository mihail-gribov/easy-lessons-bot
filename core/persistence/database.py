"""Database manager for SQLite with async/await support."""

import logging
from collections.abc import AsyncGenerator
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from settings.config import get_settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages SQLite database connection and sessions."""

    def __init__(self) -> None:
        """Initialize database manager."""
        self.settings = get_settings()
        self.engine: AsyncEngine | None = None
        self.session_factory: sessionmaker[AsyncSession] | None = None

    async def initialize(self) -> None:
        """Initialize database connection and create tables."""
        if not self.settings.database_enabled:
            logger.info("Database disabled, using in-memory storage")
            return

        try:
            # Ensure data directory exists
            db_path = Path(self.settings.database_path)
            db_path.parent.mkdir(parents=True, exist_ok=True)

            # Create async engine for SQLite
            database_url = f"sqlite+aiosqlite:///{db_path}"
            self.engine = create_async_engine(
                database_url,
                echo=False,  # Set to True for SQL debugging
                future=True,
            )

            # Create session factory
            self.session_factory = sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )

            logger.info("Database initialized successfully: %s", db_path)

        except Exception:
            logger.exception("Failed to initialize database")
            raise

    async def close(self) -> None:
        """Close database connection."""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database connection closed")

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session."""
        if not self.session_factory:
            msg = "Database not initialized"
            raise RuntimeError(msg)

        async with self.session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    @property
    def is_available(self) -> bool:
        """Check if database is available."""
        return self.settings.database_enabled and self.engine is not None


# Global database manager instance
_db_manager: DatabaseManager | None = None


def get_database_manager() -> DatabaseManager:
    """Get global database manager instance."""
    global _db_manager  # noqa: PLW0603
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


async def initialize_database() -> None:
    """Initialize global database manager."""
    db_manager = get_database_manager()
    await db_manager.initialize()


async def close_database() -> None:
    """Close global database manager."""
    db_manager = get_database_manager()
    await db_manager.close()
