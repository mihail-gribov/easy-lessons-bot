"""Migration 003: Add image analysis fields to database schema."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def upgrade(session: AsyncSession) -> None:
    """Apply migration 003: Add image analysis fields."""
    # Add new columns to sessions table
    await session.execute(text("""
        ALTER TABLE sessions ADD COLUMN last_image_analysis TEXT DEFAULT NULL;
    """))
    
    await session.execute(text("""
        ALTER TABLE sessions ADD COLUMN image_analysis_count INTEGER DEFAULT 0;
    """))

    # Add new columns to messages table
    await session.execute(text("""
        ALTER TABLE messages ADD COLUMN has_image BOOLEAN DEFAULT 0;
    """))
    
    await session.execute(text("""
        ALTER TABLE messages ADD COLUMN image_file_id TEXT DEFAULT NULL;
    """))


async def downgrade(session: AsyncSession) -> None:
    """Rollback migration 003: Remove image analysis fields."""
    # Remove columns from messages table
    await session.execute(text("""
        ALTER TABLE messages DROP COLUMN has_image;
    """))
    
    await session.execute(text("""
        ALTER TABLE messages DROP COLUMN image_file_id;
    """))

    # Remove columns from sessions table
    await session.execute(text("""
        ALTER TABLE sessions DROP COLUMN last_image_analysis;
    """))
    
    await session.execute(text("""
        ALTER TABLE sessions DROP COLUMN image_analysis_count;
    """))
