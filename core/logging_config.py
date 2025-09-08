"""Logging configuration for the application."""

import logging
from pathlib import Path


def setup_logging() -> None:
    """Set up logging configuration for the application."""
    # Create log directory if it doesn't exist
    # Use local log directory for development, /log for production
    log_dir = Path("log")
    if not log_dir.exists():
        # Try /log for production environment
        log_dir = Path("/log")
        if not log_dir.exists():
            # Fall back to local log directory
            log_dir = Path("log")

    log_dir.mkdir(exist_ok=True)

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
        handlers=[
            logging.FileHandler(log_dir / "app.log"),
            logging.StreamHandler(),  # Also log to console
        ],
    )

    # Set specific loggers
    logging.getLogger("aiogram").setLevel(logging.INFO)
    logging.getLogger("openai").setLevel(logging.WARNING)  # Reduce OpenAI noise
