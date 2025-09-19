"""Tests for updated welcome messages with image reading capability."""

import pytest
from pathlib import Path

from core.welcome_messages import get_random_welcome_message


class TestWelcomeMessagesUpdated:
    """Test that welcome messages mention image reading capability."""

    def test_welcome_messages_mention_images(self):
        """Test that welcome messages mention image reading capability."""
        base_dir = Path(__file__).parent.parent / "core" / "welcome_messages"
        files = list(base_dir.glob("*.txt"))
        
        # Should have welcome message files
        assert len(files) >= 10
        
        # All welcome messages should mention image reading capability
        image_keywords = ["картинку", "изображения", "картинка", "изображение"]
        
        for file_path in files:
            content = file_path.read_text(encoding="utf-8")
            # At least one welcome message should mention image capability
            has_image_mention = any(keyword in content.lower() for keyword in image_keywords)
            assert has_image_mention, f"Welcome message {file_path.name} should mention image reading capability"

    def test_get_random_welcome_message_returns_valid_content(self):
        """Test that get_random_welcome_message returns valid content."""
        # Test multiple calls to ensure it works
        for _ in range(5):
            message = get_random_welcome_message()
            assert message  # Should not be empty
            assert len(message) > 50  # Should be substantial
            assert isinstance(message, str)  # Should be string
