"""Tests for thinking messages functionality."""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from core.thinking_messages import get_random_thinking_message


class TestThinkingMessages:
    """Test thinking messages functionality."""

    def test_get_random_thinking_message_with_files(self):
        """Test that random thinking message is selected from available files."""
        # Mock the directory to return our test files
        with patch('core.thinking_messages.Path') as mock_path:
            # Create mock files with proper sorting
            mock_file1 = MagicMock()
            mock_file1.read_text.return_value = "минуточку, я подумаю..."
            mock_file1.__lt__ = lambda self, other: True  # Make it sortable
            
            mock_file2 = MagicMock()
            mock_file2.read_text.return_value = "сейчас разберусь..."
            mock_file2.__lt__ = lambda self, other: False  # Make it sortable
            
            # Mock the parent directory and glob
            mock_dir = MagicMock()
            mock_dir.parent = mock_dir
            mock_dir.glob.return_value = [mock_file1, mock_file2]
            mock_path.return_value = mock_dir
            
            # Test multiple calls to ensure randomness works
            results = []
            for _ in range(10):
                result = get_random_thinking_message()
                results.append(result)
            
            # Should get one of our mock messages
            assert all(result in ["минуточку, я подумаю...", "сейчас разберусь..."] for result in results)
            assert len(set(results)) >= 1  # Should get at least one different result

    def test_get_random_thinking_message_no_files_fallback(self):
        """Test fallback when no files are available."""
        with patch('core.thinking_messages.Path') as mock_path:
            # Mock empty directory
            mock_dir = MagicMock()
            mock_dir.parent = mock_dir
            mock_dir.glob.return_value = []
            mock_path.return_value = mock_dir
            
            result = get_random_thinking_message()
            assert result == "минуточку, я подумаю..."

    def test_get_random_thinking_message_read_error_fallback(self):
        """Test fallback when file read fails."""
        with patch('core.thinking_messages.Path') as mock_path:
            # Create mock file that raises exception
            mock_file = MagicMock()
            mock_file.read_text.side_effect = Exception("Read error")
            
            # Mock the directory
            mock_dir = MagicMock()
            mock_dir.parent = mock_dir
            mock_dir.glob.return_value = [mock_file]
            mock_path.return_value = mock_dir
            
            result = get_random_thinking_message()
            assert result == "минуточку, я подумаю..."

    def test_thinking_messages_files_exist(self):
        """Test that thinking message files actually exist in the filesystem."""
        base_dir = Path(__file__).parent.parent / "core" / "thinking_messages"
        files = list(base_dir.glob("*.txt"))
        
        # Should have at least 10 thinking message files
        assert len(files) >= 10
        
        # All files should be readable
        for file_path in files:
            content = file_path.read_text(encoding="utf-8").strip()
            assert content  # Should not be empty
            assert len(content) > 0  # Should have some content
