"""Tests for image processor functionality."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from core.image_processor import ImageProcessor


class TestImageProcessor:
    """Test cases for ImageProcessor class."""

    @pytest.fixture
    def image_processor(self):
        """Create ImageProcessor instance for testing."""
        return ImageProcessor()

    @pytest.fixture
    def mock_bot(self):
        """Create mock bot for testing."""
        bot = AsyncMock()
        bot.get_file = AsyncMock()
        bot.download_file = AsyncMock()
        return bot

    @pytest.fixture
    def sample_image_path(self, tmp_path):
        """Create a sample image file for testing."""
        # Create a simple test image
        from PIL import Image
        img = Image.new('RGB', (100, 100), color='red')
        img_path = tmp_path / "test_image.jpg"
        img.save(img_path)
        return img_path

    def test_get_supported_formats(self, image_processor):
        """Test getting supported image formats."""
        formats = image_processor.get_supported_formats()
        expected_formats = [".jpg", ".jpeg", ".png", ".gif", ".webp"]
        assert formats == expected_formats

    @pytest.mark.asyncio
    async def test_validate_image_file_valid(self, image_processor, sample_image_path):
        """Test validation of valid image file."""
        result = await image_processor.validate_image_file(sample_image_path)
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_image_file_nonexistent(self, image_processor):
        """Test validation of nonexistent image file."""
        nonexistent_path = Path("/nonexistent/image.jpg")
        result = await image_processor.validate_image_file(nonexistent_path)
        assert result is False

    @pytest.mark.asyncio
    async def test_validate_image_file_too_large(self, image_processor, tmp_path):
        """Test validation of too large image file."""
        # Create a large dummy file
        large_file = tmp_path / "large_image.jpg"
        large_file.write_bytes(b"x" * (21 * 1024 * 1024))  # 21MB
        
        result = await image_processor.validate_image_file(large_file)
        assert result is False

    @pytest.mark.asyncio
    async def test_prepare_image_success(self, image_processor, sample_image_path):
        """Test successful image preparation."""
        result = await image_processor.prepare_image(sample_image_path)
        assert result is not None
        assert isinstance(result, str)
        # Should be base64 encoded
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_prepare_image_invalid(self, image_processor):
        """Test image preparation with invalid file."""
        invalid_path = Path("/invalid/path.jpg")
        result = await image_processor.prepare_image(invalid_path)
        assert result is None

    @pytest.mark.asyncio
    async def test_cleanup_file(self, image_processor, tmp_path):
        """Test file cleanup functionality."""
        test_file = tmp_path / "test_cleanup.txt"
        test_file.write_text("test content")
        
        assert test_file.exists()
        await image_processor.cleanup_file(test_file)
        assert not test_file.exists()

    @pytest.mark.asyncio
    async def test_cleanup_nonexistent_file(self, image_processor):
        """Test cleanup of nonexistent file."""
        nonexistent_path = Path("/nonexistent/file.txt")
        # Should not raise exception
        await image_processor.cleanup_file(nonexistent_path)

    @pytest.mark.asyncio
    @patch('core.image_processor.openai.AsyncOpenAI')
    async def test_analyze_with_vision_api_success(self, mock_openai, image_processor):
        """Test successful Vision API analysis."""
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"content_type": "math_problem", "extracted_text": "2+2=?", "subject": "mathematics", "topic": "arithmetic", "complexity_level": 2, "questions": ["What is 2+2?"], "context_match": false, "educational_value": "high", "confidence": 0.9}'
        
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_openai.return_value = mock_client
        
        # Replace the client in the processor
        image_processor.openai_client = mock_client
        
        result = await image_processor._analyze_with_vision_api("base64data", {})
        
        assert "content_type" in result
        assert result["content_type"] == "math_problem"
        assert result["extracted_text"] == "2+2=?"
        assert result["subject"] == "mathematics"

    @pytest.mark.asyncio
    @patch('core.image_processor.openai.AsyncOpenAI')
    async def test_analyze_with_vision_api_json_error(self, mock_openai, image_processor):
        """Test Vision API analysis with JSON parsing error."""
        # Mock OpenAI response with invalid JSON
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Invalid JSON response"
        
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_openai.return_value = mock_client
        
        # Replace the client in the processor
        image_processor.openai_client = mock_client
        
        result = await image_processor._analyze_with_vision_api("base64data", {})
        
        # Should return fallback result
        assert result["content_type"] == "unknown"
        assert result["confidence"] == 0.5

    @pytest.mark.asyncio
    async def test_download_image_success(self, image_processor, mock_bot, tmp_path):
        """Test successful image download."""
        # Setup mock bot
        image_processor.bot = mock_bot
        
        # Mock file info
        mock_file = MagicMock()
        mock_file.file_path = "photos/file_123.jpg"
        mock_bot.get_file.return_value = mock_file
        
        # Mock file content
        mock_content = MagicMock()
        mock_content.read.return_value = b"fake image data"
        mock_bot.download_file.return_value = mock_content
        
        # Mock tempfile to use our tmp_path
        with patch('tempfile.NamedTemporaryFile') as mock_temp:
            mock_temp_file = MagicMock()
            mock_temp_file.name = str(tmp_path / "temp_image.jpg")
            mock_temp.return_value = mock_temp_file
            
            result = await image_processor.download_image("file_123")
            
            assert result is not None
            assert result.exists()
            assert result.read_bytes() == b"fake image data"

    @pytest.mark.asyncio
    async def test_download_image_no_bot(self, image_processor):
        """Test image download without bot instance."""
        result = await image_processor.download_image("file_123")
        assert result is None

    @pytest.mark.asyncio
    async def test_download_image_failed_get_file(self, image_processor, mock_bot):
        """Test image download with failed get_file."""
        image_processor.bot = mock_bot
        mock_bot.get_file.return_value = None
        
        result = await image_processor.download_image("file_123")
        assert result is None

    @pytest.mark.asyncio
    async def test_download_image_failed_download(self, image_processor, mock_bot):
        """Test image download with failed download_file."""
        image_processor.bot = mock_bot
        
        # Mock file info
        mock_file = MagicMock()
        mock_file.file_path = "photos/file_123.jpg"
        mock_bot.get_file.return_value = mock_file
        
        # Mock failed download
        mock_bot.download_file.return_value = None
        
        result = await image_processor.download_image("file_123")
        assert result is None
