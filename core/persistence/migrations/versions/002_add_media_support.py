"""Migration 002: Add media support to database schema."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def upgrade(session: AsyncSession) -> None:
    """Apply migration 002: Add media support."""
    # Add new columns to sessions table
    await session.execute(text("""
        ALTER TABLE sessions ADD COLUMN media_context TEXT DEFAULT '{}';
    """))
    
    await session.execute(text("""
        ALTER TABLE sessions ADD COLUMN audio_enabled BOOLEAN DEFAULT 1;
    """))
    
    await session.execute(text("""
        ALTER TABLE sessions ADD COLUMN image_analysis_history TEXT DEFAULT '[]';
    """))

    # Create media_files table
    await session.execute(text("""
        CREATE TABLE media_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT NOT NULL,
            file_id TEXT NOT NULL,
            file_type TEXT NOT NULL CHECK (file_type IN ('audio', 'image', 'document')),
            content_type TEXT NOT NULL,
            analysis_result TEXT DEFAULT '{}',
            context_match BOOLEAN DEFAULT 0,
            processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (chat_id) REFERENCES sessions (chat_id)
        );
    """))

    # Create indexes for better performance
    await session.execute(text("""
        CREATE INDEX idx_media_files_chat_id ON media_files (chat_id);
    """))
    
    await session.execute(text("""
        CREATE INDEX idx_media_files_file_type ON media_files (file_type);
    """))
    
    await session.execute(text("""
        CREATE INDEX idx_media_files_processed_at ON media_files (processed_at);
    """))


async def downgrade(session: AsyncSession) -> None:
    """Rollback migration 002: Remove media support."""
    # Drop media_files table
    await session.execute(text("DROP TABLE IF EXISTS media_files;"))
    
    # Remove columns from sessions table
    await session.execute(text("""
        ALTER TABLE sessions DROP COLUMN media_context;
    """))
    
    await session.execute(text("""
        ALTER TABLE sessions DROP COLUMN audio_enabled;
    """))
    
    await session.execute(text("""
        ALTER TABLE sessions DROP COLUMN image_analysis_history;
    """))
