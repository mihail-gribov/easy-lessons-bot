"""Initial database schema migration."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def upgrade(session: AsyncSession) -> None:
    """Apply initial schema migration."""
    # Create sessions table
    await session.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                chat_id TEXT PRIMARY KEY,
                scenario TEXT NOT NULL DEFAULT 'unknown',
                question TEXT,
                topic TEXT,
                is_new_question BOOLEAN NOT NULL DEFAULT 0,
                is_new_topic BOOLEAN NOT NULL DEFAULT 0,
                understanding_level INTEGER NOT NULL DEFAULT 0,
                previous_understanding_level INTEGER,
                previous_topic TEXT,
                user_preferences TEXT NOT NULL DEFAULT '[]',
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    )

    # Create messages table
    await session.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (chat_id) REFERENCES sessions (chat_id)
            )
            """
        )
    )

    # Create migrations table
    await session.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS migrations (
                version INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    )

    # Create indexes for better performance
    await session.execute(
        text("CREATE INDEX IF NOT EXISTS idx_messages_chat_id ON messages (chat_id)")
    )
    await session.execute(
        text(
            "CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages (timestamp)"
        )
    )


async def downgrade(session: AsyncSession) -> None:
    """Rollback initial schema migration."""
    await session.execute(text("DROP TABLE IF EXISTS messages"))
    await session.execute(text("DROP TABLE IF EXISTS sessions"))
    await session.execute(text("DROP TABLE IF EXISTS migrations"))
