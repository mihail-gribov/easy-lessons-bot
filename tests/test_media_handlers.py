"""Tests for media handlers functionality."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram.types import Message, Voice, PhotoSize, Document, User, Chat

from bot.media_handlers import MediaHandlers


class TestMediaHandlers:
    """Test cases for MediaHandlers."""

    @pytest.fixture
    def media_handlers(self):
        """Create MediaHandlers instance for testing."""
        # Create a mock bot for testing
        mock_bot = MagicMock()
        return MediaHandlers(mock_bot)

    @pytest.fixture
    def mock_message(self):
        """Create mock Telegram message for testing."""
        message = MagicMock()
        message.chat = MagicMock()
        message.chat.id = 12345
        message.from_user = MagicMock()
        message.from_user.id = 67890
        return message

    @pytest.fixture
    def mock_voice_message(self, mock_message):
        """Create mock voice message for testing."""
        voice = MagicMock(spec=Voice)
        voice.file_id = "test_voice_file_id"
        mock_message.voice = voice
        return mock_message

    @pytest.fixture
    def mock_photo_message(self, mock_message):
        """Create mock photo message for testing."""
        photo = MagicMock(spec=PhotoSize)
        photo.file_id = "test_photo_file_id"
        mock_message.photo = [photo]
        return mock_message

    @pytest.fixture
    def mock_document_message(self, mock_message):
        """Create mock document message for testing."""
        document = MagicMock(spec=Document)
        document.file_id = "test_document_file_id"
        document.mime_type = "image/jpeg"
        mock_message.document = document
        return mock_message

    @pytest.mark.asyncio
    async def test_handle_voice_message_success(self, media_handlers, mock_voice_message):
        """Test successful voice message handling."""
        with patch.object(media_handlers.media_processor, 'process_media') as mock_process, \
             patch.object(media_handlers.audio_handler, 'analyze_audio_intent') as mock_analyze, \
             patch.object(media_handlers.context_matcher, 'match_context') as mock_match, \
             patch.object(media_handlers.session_manager, 'get_session') as mock_get_session, \
             patch.object(media_handlers.session_manager, 'save_session') as mock_save_session:
            
            # Mock session
            mock_session = MagicMock()
            mock_session.to_dict.return_value = {"topic": "math", "scenario": "discussion"}
            mock_get_session.return_value = mock_session

            # Mock media processing
            mock_process.return_value = {
                "type": "audio",
                "transcript": "What is 2 plus 2?",
                "intent": "question",
                "subject": "math",
                "topic": "addition",
                "understanding_level": 3
            }

            # Mock intent analysis
            mock_analyze.return_value = {
                "intent": "question",
                "subject": "math",
                "topic": "addition",
                "understanding_level": 3,
                "context": "Audio intent analysis"
            }

            # Mock context matching
            mock_match.return_value = {
                "scenario": "explanation",
                "context_relation": "direct_continuation",
                "topic_continuation": True,
                "response_approach": "simple_step_by_step",
                "educational_focus": "foundational_concepts",
                "media_integration": "use_as_example"
            }

            result = await media_handlers.handle_voice_message(mock_voice_message, None)

            assert result is not None
            assert "аудио" in result.lower() or "голосовое" in result.lower()
            mock_process.assert_called_once()
            mock_analyze.assert_called_once()
            mock_match.assert_called_once()
            mock_save_session.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_voice_message_processing_error(self, media_handlers, mock_voice_message):
        """Test voice message handling with processing error."""
        with patch.object(media_handlers.media_processor, 'process_media') as mock_process, \
             patch.object(media_handlers.session_manager, 'get_session') as mock_get_session:
            
            mock_session = MagicMock()
            mock_session.to_dict.return_value = {}
            mock_get_session.return_value = mock_session

            mock_process.return_value = {"error": "Processing failed"}

            result = await media_handlers.handle_voice_message(mock_voice_message, None)

            assert result is not None
            assert "не удалось обработать" in result.lower()

    @pytest.mark.asyncio
    async def test_handle_photo_message_success(self, media_handlers, mock_photo_message):
        """Test successful photo message handling."""
        with patch.object(media_handlers.media_processor, 'process_media') as mock_process, \
             patch.object(media_handlers.context_matcher, 'match_context') as mock_match, \
             patch.object(media_handlers.session_manager, 'get_session') as mock_get_session, \
             patch.object(media_handlers.session_manager, 'save_session') as mock_save_session:
            
            # Mock session
            mock_session = MagicMock()
            mock_session.to_dict.return_value = {"topic": "math", "scenario": "discussion"}
            mock_get_session.return_value = mock_session

            # Mock media processing
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

            # Mock context matching
            mock_match.return_value = {
                "scenario": "explanation",
                "context_relation": "direct_continuation",
                "topic_continuation": True,
                "response_approach": "simple_step_by_step",
                "educational_focus": "foundational_concepts",
                "media_integration": "use_as_example"
            }

            result = await media_handlers.handle_photo_message(mock_photo_message, None)

            assert result is not None
            assert "изображении" in result.lower() or "фото" in result.lower()
            mock_process.assert_called_once()
            mock_match.assert_called_once()
            mock_save_session.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_document_message_image(self, media_handlers, mock_document_message):
        """Test document message handling for image document."""
        with patch.object(media_handlers.media_processor, 'process_media') as mock_process, \
             patch.object(media_handlers.context_matcher, 'match_context') as mock_match, \
             patch.object(media_handlers.session_manager, 'get_session') as mock_get_session, \
             patch.object(media_handlers.session_manager, 'save_session') as mock_save_session:
            
            # Mock session
            mock_session = MagicMock()
            mock_session.to_dict.return_value = {"topic": "science", "scenario": "discussion"}
            mock_get_session.return_value = mock_session

            # Mock media processing
            mock_process.return_value = {
                "type": "image",
                "content_type": "diagram",
                "extracted_text": "Plant diagram",
                "subject": "science",
                "topic": "photosynthesis",
                "complexity_level": 5,
                "questions": [],
                "context_match": False,
                "educational_value": "medium"
            }

            # Mock context matching
            mock_match.return_value = {
                "scenario": "explanation",
                "context_relation": "new_topic",
                "topic_continuation": False,
                "response_approach": "structured_explanation",
                "educational_focus": "practical_application",
                "media_integration": "use_as_example"
            }

            result = await media_handlers.handle_document_message(mock_document_message, None)

            assert result is not None
            assert "документ" in result.lower() or "изображении" in result.lower()
            mock_process.assert_called_once()
            mock_match.assert_called_once()
            mock_save_session.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_document_message_non_image(self, media_handlers, mock_document_message):
        """Test document message handling for non-image document."""
        mock_document_message.document.mime_type = "application/pdf"

        result = await media_handlers.handle_document_message(mock_document_message, None)

        assert result is not None
        assert "только изображения" in result.lower()

    @pytest.mark.asyncio
    async def test_generate_media_response_explanation(self, media_handlers):
        """Test media response generation for explanation scenario."""
        media_result = {
            "type": "image",
            "content_type": "math_problem",
            "extracted_text": "2 + 2 = ?",
            "topic": "addition",
            "subject": "math"
        }
        
        context_result = {
            "scenario": "explanation",
            "context_relation": "direct_continuation",
            "topic_continuation": True,
            "response_approach": "simple_step_by_step",
            "educational_focus": "foundational_concepts",
            "media_integration": "use_as_example"
        }
        
        session_context = {"understanding_level": 3}

        result = await media_handlers._generate_media_response(
            media_result, context_result, session_context
        )

        assert result is not None
        assert "разберем" in result.lower() or "объясн" in result.lower()

    @pytest.mark.asyncio
    async def test_generate_media_response_discussion(self, media_handlers):
        """Test media response generation for discussion scenario."""
        media_result = {
            "type": "audio",
            "transcript": "Tell me about math",
            "topic": "mathematics",
            "subject": "math"
        }
        
        context_result = {
            "scenario": "discussion",
            "context_relation": "direct_continuation",
            "topic_continuation": True,
            "response_approach": "interactive_discussion",
            "educational_focus": "practical_application",
            "media_integration": "reference_in_context"
        }
        
        session_context = {"understanding_level": 5}

        result = await media_handlers._generate_media_response(
            media_result, context_result, session_context
        )

        assert result is not None
        assert "обсудим" in result.lower() or "продолж" in result.lower()

    @pytest.mark.asyncio
    async def test_generate_media_response_general(self, media_handlers):
        """Test media response generation for general scenario."""
        media_result = {
            "type": "image",
            "content_type": "unknown",
            "topic": "unknown",
            "subject": "unknown"
        }
        
        context_result = {
            "scenario": "unknown",
            "context_relation": "unrelated",
            "topic_continuation": False,
            "response_approach": "general",
            "educational_focus": "basic",
            "media_integration": "minimal"
        }
        
        session_context = {}

        result = await media_handlers._generate_media_response(
            media_result, context_result, session_context
        )

        assert result is not None
        assert "помочь" in result.lower() or "расскажите" in result.lower()
