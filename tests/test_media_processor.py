"""Tests for media processor functionality."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from core.media_processor import MediaProcessor


class TestMediaProcessor:
    """Test cases for MediaProcessor."""

    @pytest.fixture
    def media_processor(self):
        """Create MediaProcessor instance for testing."""
        with patch('core.media_processor.get_settings') as mock_settings:
            mock_settings.return_value.audio_enabled = True
            mock_settings.return_value.image_analysis_enabled = True
            mock_settings.return_value.temp_dir = "data/temp"
            # Create a mock bot for testing
            mock_bot = MagicMock()
            return MediaProcessor(mock_bot)

    @pytest.mark.asyncio
    async def test_process_media_audio(self, media_processor):
        """Test processing audio media."""
        with patch.object(media_processor, '_download_file') as mock_download, \
             patch.object(media_processor, '_process_audio') as mock_process, \
             patch.object(media_processor, '_cleanup_file') as mock_cleanup:
            
            mock_download.return_value = Path("test_audio.ogg")
            mock_process.return_value = {
                "type": "audio",
                "transcript": "Test audio transcript",
                "intent": "question",
                "subject": "math",
                "topic": "addition",
                "understanding_level": 5,
                "context": "Test context"
            }

            result = await media_processor.process_media(
                file_id="test_file_id",
                file_type="audio",
                chat_id="test_chat_id",
                session_context={}
            )

            assert result["type"] == "audio"
            assert result["transcript"] == "Test audio transcript"
            mock_download.assert_called_once_with("test_file_id", "audio")
            mock_process.assert_called_once()
            mock_cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_media_image(self, media_processor):
        """Test processing image media."""
        with patch.object(media_processor, '_download_file') as mock_download, \
             patch.object(media_processor, '_process_image') as mock_process, \
             patch.object(media_processor, '_cleanup_file') as mock_cleanup:
            
            mock_download.return_value = Path("test_image.jpg")
            mock_process.return_value = {
                "type": "image",
                "content_type": "math_problem",
                "extracted_text": "2 + 2 = ?",
                "subject": "math",
                "topic": "addition",
                "complexity_level": 3,
                "questions": ["What is 2 + 2?"],
                "context_match": True,
                "educational_value": "high"
            }

            result = await media_processor.process_media(
                file_id="test_file_id",
                file_type="image",
                chat_id="test_chat_id",
                session_context={}
            )

            assert result["type"] == "image"
            assert result["content_type"] == "math_problem"
            mock_download.assert_called_once_with("test_file_id", "image")
            mock_process.assert_called_once()
            mock_cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_media_unsupported_type(self, media_processor):
        """Test processing unsupported media type."""
        result = await media_processor.process_media(
            file_id="test_file_id",
            file_type="video",
            chat_id="test_chat_id",
            session_context={}
        )

        assert "error" in result
        assert "Unsupported file type" in result["error"]

    @pytest.mark.asyncio
    async def test_process_media_download_failure(self, media_processor):
        """Test processing when file download fails."""
        with patch.object(media_processor, '_download_file') as mock_download:
            mock_download.return_value = None

            result = await media_processor.process_media(
                file_id="test_file_id",
                file_type="audio",
                chat_id="test_chat_id",
                session_context={}
            )

            assert "error" in result
            assert "Failed to download file" in result["error"]

    @pytest.mark.asyncio
    async def test_is_media_supported(self, media_processor):
        """Test media type support checking."""
        # Test supported types
        assert await media_processor.is_media_supported("audio") is True
        assert await media_processor.is_media_supported("voice") is True
        assert await media_processor.is_media_supported("image") is True
        assert await media_processor.is_media_supported("photo") is True
        
        # Test unsupported types
        assert await media_processor.is_media_supported("video") is False
        assert await media_processor.is_media_supported("document") is False

    def test_get_file_suffix(self, media_processor):
        """Test file suffix mapping."""
        assert media_processor._get_file_suffix("audio") == ".ogg"
        assert media_processor._get_file_suffix("voice") == ".ogg"
        assert media_processor._get_file_suffix("image") == ".jpg"
        assert media_processor._get_file_suffix("photo") == ".jpg"
        assert media_processor._get_file_suffix("document") == ".pdf"
        assert media_processor._get_file_suffix("unknown") == ".tmp"

    @pytest.mark.asyncio
    async def test_cleanup_file(self, media_processor):
        """Test file cleanup functionality."""
        with patch('pathlib.Path.exists') as mock_exists, \
             patch('pathlib.Path.unlink') as mock_unlink:
            
            mock_exists.return_value = True
            test_path = Path("test_file.tmp")
            
            await media_processor._cleanup_file(test_path)
            
            mock_unlink.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_nonexistent_file(self, media_processor):
        """Test cleanup of non-existent file."""
        with patch('pathlib.Path.exists') as mock_exists, \
             patch('pathlib.Path.unlink') as mock_unlink:
            
            mock_exists.return_value = False
            test_path = Path("nonexistent_file.tmp")
            
            await media_processor._cleanup_file(test_path)
            
            mock_unlink.assert_not_called()
