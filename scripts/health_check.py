#!/usr/bin/env python3
"""Health check script for Easy Lessons Bot."""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from core.persistence import get_database_manager
    from core.version_info import format_version_info
    from settings.config import get_settings
except ImportError as e:
    print(f"Health check failed: Import error - {e}")
    sys.exit(1)


async def health_check() -> bool:
    """Perform comprehensive health check."""
    try:
        # Check configuration
        settings = get_settings()
        
        # Check database if enabled
        if settings.database_enabled:
            try:
                from core.persistence import initialize_database
                
                # Initialize database first
                await initialize_database()
                
                db_manager = get_database_manager()
                if db_manager is None:
                    print("Health check failed: Database manager not available")
                    return False
                
                # Test database connection
                if db_manager.is_available:
                    print(f"Health check passed: {format_version_info()}, Database OK")
                else:
                    print(f"Health check failed: Database not available")
                    return False
            except Exception as e:
                print(f"Health check failed: Database error - {e}")
                return False
        else:
            print(f"Health check passed: {format_version_info()}, In-memory mode")
            
        return True
        
    except Exception as e:
        print(f"Health check failed: {e}")
        return False


if __name__ == "__main__":
    result = asyncio.run(health_check())
    sys.exit(0 if result else 1)
