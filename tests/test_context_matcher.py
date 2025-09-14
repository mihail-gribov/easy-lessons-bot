"""Tests for context matcher functionality."""

import pytest
from unittest.mock import MagicMock

from core.context_matcher import ContextMatcher


class TestContextMatcher:
    """Test cases for ContextMatcher."""

    @pytest.fixture
    def context_matcher(self):
        """Create ContextMatcher instance for testing."""
        return ContextMatcher()

    @pytest.mark.asyncio
    async def test_match_context_audio_related_topic(self, context_matcher):
        """Test context matching for audio with related topic."""
        media_analysis = {
            "type": "audio",
            "subject": "math",
            "topic": "addition",
            "transcript": "What is 2 plus 2?",
            "intent": "question",
            "understanding_level": 3
        }
        
        session_context = {
            "topic": "addition",
            "scenario": "discussion",
            "understanding_level": 3
        }

        result = await context_matcher.match_context(media_analysis, session_context)

        assert result["scenario"] == "discussion"
        assert result["context_relation"] == "direct_continuation"
        assert result["topic_continuation"] is True
        assert result["response_approach"] in ["interactive_discussion", "simple_step_by_step"]

    @pytest.mark.asyncio
    async def test_match_context_image_new_topic(self, context_matcher):
        """Test context matching for image with new topic."""
        media_analysis = {
            "type": "image",
            "subject": "science",
            "topic": "photosynthesis",
            "content_type": "diagram",
            "extracted_text": "Plant diagram showing photosynthesis",
            "complexity_level": 5
        }
        
        session_context = {
            "topic": "math",
            "scenario": "discussion",
            "understanding_level": 5
        }

        result = await context_matcher.match_context(media_analysis, session_context)

        assert result["scenario"] == "explanation"
        assert result["context_relation"] == "new_topic"
        assert result["topic_continuation"] is False
        assert result["response_approach"] in ["structured_explanation", "detailed_analysis"]

    @pytest.mark.asyncio
    async def test_match_context_questions_detected(self, context_matcher):
        """Test context matching when questions are detected in media."""
        media_analysis = {
            "type": "image",
            "subject": "math",
            "topic": "algebra",
            "content_type": "math_problem",
            "questions": ["Solve for x: 2x + 3 = 7"],
            "complexity_level": 6
        }
        
        session_context = {
            "topic": "algebra",
            "scenario": "unknown",
            "understanding_level": 6
        }

        result = await context_matcher.match_context(media_analysis, session_context)

        assert result["scenario"] == "discussion"
        assert result["response_approach"] in ["interactive_discussion", "structured_explanation", "detailed_analysis"]

    @pytest.mark.asyncio
    async def test_match_context_no_session_context(self, context_matcher):
        """Test context matching without session context."""
        media_analysis = {
            "type": "audio",
            "subject": "history",
            "topic": "ancient civilizations",
            "transcript": "Tell me about ancient Egypt",
            "intent": "question",
            "understanding_level": 4
        }

        result = await context_matcher.match_context(media_analysis, None)

        assert result["scenario"] == "explanation"
        assert result["context_relation"] == "unrelated"
        assert result["topic_continuation"] is False

    @pytest.mark.asyncio
    async def test_match_context_unknown_media_type(self, context_matcher):
        """Test context matching for unknown media type."""
        media_analysis = {
            "type": "unknown",
            "subject": "",
            "topic": "",
            "complexity_level": 5
        }
        
        session_context = {
            "topic": "math",
            "scenario": "discussion",
            "understanding_level": 5
        }

        result = await context_matcher.match_context(media_analysis, session_context)

        assert result["scenario"] == "discussion"
        assert result["response_approach"] == "interactive_discussion"

    def test_topics_related_same_topic(self, context_matcher):
        """Test topic relation detection for same topics."""
        assert context_matcher._topics_related("addition", "addition") is True
        assert context_matcher._topics_related("math", "math") is True

    def test_topics_related_related_topics(self, context_matcher):
        """Test topic relation detection for related topics."""
        assert context_matcher._topics_related("addition", "basic addition") is True
        assert context_matcher._topics_related("math problems", "math") is True
        assert context_matcher._topics_related("algebra", "algebraic equations") is True

    def test_topics_related_unrelated_topics(self, context_matcher):
        """Test topic relation detection for unrelated topics."""
        assert context_matcher._topics_related("math", "history") is False
        assert context_matcher._topics_related("science", "literature") is False
        assert context_matcher._topics_related("addition", "photosynthesis") is False

    def test_topics_related_empty_topics(self, context_matcher):
        """Test topic relation detection for empty topics."""
        assert context_matcher._topics_related("", "math") is False
        assert context_matcher._topics_related("math", "") is False
        assert context_matcher._topics_related("", "") is False

    def test_determine_educational_focus_low_level(self, context_matcher):
        """Test educational focus determination for low understanding level."""
        media_analysis = {"complexity_level": 2}
        understanding_level = 2

        result = context_matcher._determine_educational_focus(media_analysis, understanding_level)
        assert result == "foundational_concepts"

    def test_determine_educational_focus_medium_level(self, context_matcher):
        """Test educational focus determination for medium understanding level."""
        media_analysis = {"complexity_level": 5}
        understanding_level = 5

        result = context_matcher._determine_educational_focus(media_analysis, understanding_level)
        assert result == "practical_application"

    def test_determine_educational_focus_high_level(self, context_matcher):
        """Test educational focus determination for high understanding level."""
        media_analysis = {"complexity_level": 8}
        understanding_level = 8

        result = context_matcher._determine_educational_focus(media_analysis, understanding_level)
        assert result == "advanced_analysis"

    def test_determine_media_integration_explanation(self, context_matcher):
        """Test media integration approach for explanation scenario."""
        media_analysis = {"type": "image"}
        scenario = "explanation"

        result = context_matcher._determine_media_integration(media_analysis, scenario)
        assert result == "use_as_example"

    def test_determine_media_integration_discussion(self, context_matcher):
        """Test media integration approach for discussion scenario."""
        media_analysis = {"type": "audio"}
        scenario = "discussion"

        result = context_matcher._determine_media_integration(media_analysis, scenario)
        assert result == "reference_in_context"

    def test_determine_media_integration_unknown(self, context_matcher):
        """Test media integration approach for unknown scenario."""
        media_analysis = {"type": "image"}
        scenario = "unknown"

        result = context_matcher._determine_media_integration(media_analysis, scenario)
        assert result == "acknowledge_content"
