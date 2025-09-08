"""Main entry point for the Easy Lessons Bot application."""

import logging

from core.logging_config import setup_logging


def main() -> None:
    """Main application entry point."""
    # Set up logging
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("Easy Lessons Bot starting up...")
    logger.info("Logging configured successfully")

    # Initialize bot and other components in future iterations
    logger.info("Application ready (basic setup complete)")


if __name__ == "__main__":
    main()
