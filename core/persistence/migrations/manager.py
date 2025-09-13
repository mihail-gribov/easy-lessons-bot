"""Migration manager for database schema updates."""

import logging
from pathlib import Path
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.persistence.database import get_database_manager
from core.persistence.models import Base, Migration

logger = logging.getLogger(__name__)


class MigrationManager:
    """Manages database migrations."""

    def __init__(self) -> None:
        """Initialize migration manager."""
        self.db_manager = get_database_manager()
        self.migrations_dir = Path(__file__).parent / "versions"

    async def initialize(self) -> None:
        """Initialize migration system and apply pending migrations."""
        if not self.db_manager.is_available:
            logger.info("Database not available, skipping migrations")
            return

        try:
            # Create tables if they don't exist
            async with self.db_manager.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
                logger.info("Database tables created/verified")

            # Apply pending migrations
            await self.apply_migrations()

        except Exception:
            logger.exception("Failed to initialize migrations")
            raise

    async def apply_migrations(self) -> None:
        """Apply all pending migrations."""
        if not self.db_manager.is_available:
            return

        try:
            # Get list of available migration files
            migration_files = sorted(
                [f for f in self.migrations_dir.glob("*.py") if f.name != "__init__.py"]
            )

            if not migration_files:
                logger.info("No migration files found")
                return

            session_gen = self.db_manager.get_session()
            session = await session_gen.__anext__()
            try:
                # Get applied migrations
                applied_migrations = await self._get_applied_migrations(session)

                # Apply pending migrations
                for migration_file in migration_files:
                    version = int(migration_file.stem.split("_")[0])
                    if version not in applied_migrations:
                        await self._apply_migration(session, migration_file, version)
            finally:
                await session_gen.aclose()

        except Exception:
            logger.exception("Failed to apply migrations")
            raise

    async def _get_applied_migrations(self, session: AsyncSession) -> set[int]:
        """Get set of applied migration versions."""
        try:
            result = await session.execute(text("SELECT version FROM migrations"))
            return {row[0] for row in result.fetchall()}
        except Exception:  # noqa: BLE001
            # Table doesn't exist yet, return empty set
            return set()

    async def _apply_migration(
        self, session: AsyncSession, migration_file: Path, version: int
    ) -> None:
        """Apply a single migration."""
        try:
            logger.info("Applying migration: %s", migration_file.name)

            # Import and execute migration
            migration_module = self._import_migration(migration_file)
            await migration_module.upgrade(session)

            # Record migration as applied
            migration_record = Migration(
                version=version,
                name=migration_file.stem,
            )
            session.add(migration_record)
            await session.commit()

            logger.info("Migration %d applied successfully", version)

        except Exception:
            logger.exception("Failed to apply migration %d", version)
            await session.rollback()
            raise

    def _import_migration(self, migration_file: Path) -> Any:
        """Import migration module dynamically."""
        import importlib.util
        import sys

        spec = importlib.util.spec_from_file_location(
            migration_file.stem, migration_file
        )
        if spec is None or spec.loader is None:
            msg = f"Could not load migration {migration_file}"
            raise ImportError(msg)

        module = importlib.util.module_from_spec(spec)
        sys.modules[migration_file.stem] = module
        spec.loader.exec_module(module)

        return module

    async def get_migration_status(self) -> dict[str, Any]:
        """Get current migration status."""
        if not self.db_manager.is_available:
            return {"status": "database_disabled"}

        try:
            session_gen = self.db_manager.get_session()
            session = await session_gen.__anext__()
            try:
                applied_migrations = await self._get_applied_migrations(session)
                migration_files = sorted(
                    [
                        f
                        for f in self.migrations_dir.glob("*.py")
                        if f.name != "__init__.py"
                    ]
                )

                return {
                    "status": "available",
                    "applied_migrations": list(applied_migrations),
                    "total_migrations": len(migration_files),
                    "pending_migrations": [
                        int(f.stem.split("_")[0])
                        for f in migration_files
                        if int(f.stem.split("_")[0]) not in applied_migrations
                    ],
                }
            finally:
                await session_gen.aclose()

        except Exception as e:
            logger.exception("Failed to get migration status")
            return {"status": "error", "error": str(e)}


# Global migration manager instance
_migration_manager: MigrationManager | None = None


def get_migration_manager() -> MigrationManager:
    """Get global migration manager instance."""
    global _migration_manager  # noqa: PLW0603
    if _migration_manager is None:
        _migration_manager = MigrationManager()
    return _migration_manager


async def initialize_migrations() -> None:
    """Initialize global migration manager."""
    migration_manager = get_migration_manager()
    await migration_manager.initialize()
