"""Context matching for media content with conversation context."""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ContextMatcher:
    """Matches media content with current conversation context."""

    def __init__(self):
        """Initialize context matcher."""
        pass

    async def match_context(
        self,
        media_analysis: Dict[str, Any],
        session_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Match media content with current conversation context.

        Args:
            media_analysis: Results from media analysis
            session_context: Current session context

        Returns:
            Context matching results
        """
        try:
            logger.info("Matching media content with conversation context")

            if not session_context:
                session_context = {}

            # Extract current context
            current_topic = session_context.get("topic", "")
            current_scenario = session_context.get("scenario", "unknown")
            understanding_level = session_context.get("understanding_level", 5)

            # Analyze media content
            media_type = media_analysis.get("type", "unknown")
            media_subject = media_analysis.get("subject", "")
            media_topic = media_analysis.get("topic", "")

            # Determine scenario
            scenario = self._determine_scenario(
                media_analysis, current_topic, current_scenario
            )

            # Determine context relation
            context_relation = self._determine_context_relation(
                media_topic, current_topic, media_subject
            )

            # Determine response approach
            response_approach = self._determine_response_approach(
                scenario, understanding_level, media_analysis
            )

            result = {
                "scenario": scenario,
                "context_relation": context_relation,
                "topic_continuation": self._should_continue_topic(
                    media_topic, current_topic
                ),
                "response_approach": response_approach,
                "educational_focus": self._determine_educational_focus(
                    media_analysis, understanding_level
                ),
                "media_integration": self._determine_media_integration(
                    media_analysis, scenario
                ),
            }

            logger.info(f"Context matching result: {result}")
            return result

        except Exception as e:
            logger.error(f"Error in context matching: {e}", exc_info=True)
            return {
                "scenario": "unknown",
                "context_relation": "unrelated",
                "topic_continuation": False,
                "response_approach": "general",
                "educational_focus": "basic",
                "media_integration": "minimal",
            }

    def _determine_scenario(
        self,
        media_analysis: Dict[str, Any],
        current_topic: str,
        current_scenario: str,
    ) -> str:
        """
        Determine the best scenario for response.

        Args:
            media_analysis: Media analysis results
            current_topic: Current conversation topic
            current_scenario: Current conversation scenario

        Returns:
            Scenario name
        """
        media_type = media_analysis.get("type", "unknown")
        media_subject = media_analysis.get("subject", "")
        media_topic = media_analysis.get("topic", "")

        # If media has clear educational content
        if media_subject and media_topic:
            # Check if it relates to current topic
            if self._topics_related(media_topic, current_topic):
                return "discussion"
            else:
                return "explanation"  # New topic to explain

        # If media has questions or problems
        questions = media_analysis.get("questions", [])
        if questions and len(questions) > 0:
            return "explanation"

        # Default to current scenario or unknown
        return current_scenario if current_scenario != "unknown" else "unknown"

    def _determine_context_relation(
        self, media_topic: str, current_topic: str, media_subject: str
    ) -> str:
        """
        Determine how media relates to current conversation.

        Args:
            media_topic: Media topic
            current_topic: Current conversation topic
            media_subject: Media subject

        Returns:
            Context relation description
        """
        if not media_topic or not current_topic:
            return "unrelated"

        if self._topics_related(media_topic, current_topic):
            return "direct_continuation"
        elif media_subject and current_topic and media_subject.lower() in current_topic.lower():
            return "same_subject"
        else:
            return "new_topic"

    def _determine_response_approach(
        self,
        scenario: str,
        understanding_level: int,
        media_analysis: Dict[str, Any],
    ) -> str:
        """
        Determine how to structure the response.

        Args:
            scenario: Determined scenario
            understanding_level: Current understanding level
            media_analysis: Media analysis results

        Returns:
            Response approach
        """
        if scenario == "explanation":
            if understanding_level <= 3:
                return "simple_step_by_step"
            elif understanding_level <= 6:
                return "structured_explanation"
            else:
                return "detailed_analysis"
        elif scenario == "discussion":
            return "interactive_discussion"
        else:
            return "general_response"

    def _should_continue_topic(self, media_topic: str, current_topic: str) -> bool:
        """
        Determine if we should continue current topic.

        Args:
            media_topic: Media topic
            current_topic: Current conversation topic

        Returns:
            True if should continue, False otherwise
        """
        if not media_topic or not current_topic:
            return False
        return self._topics_related(media_topic, current_topic)

    def _determine_educational_focus(
        self, media_analysis: Dict[str, Any], understanding_level: int
    ) -> str:
        """
        Determine educational focus for response.

        Args:
            media_analysis: Media analysis results
            understanding_level: Current understanding level

        Returns:
            Educational focus
        """
        media_complexity = media_analysis.get("complexity_level", 5)
        
        if understanding_level <= 3 or media_complexity <= 3:
            return "foundational_concepts"
        elif understanding_level <= 6 or media_complexity <= 6:
            return "practical_application"
        else:
            return "advanced_analysis"

    def _determine_media_integration(
        self, media_analysis: Dict[str, Any], scenario: str
    ) -> str:
        """
        Determine how to integrate media insights.

        Args:
            media_analysis: Media analysis results
            scenario: Determined scenario

        Returns:
            Media integration approach
        """
        if scenario == "explanation":
            return "use_as_example"
        elif scenario == "discussion":
            return "reference_in_context"
        else:
            return "acknowledge_content"

    def _topics_related(self, topic1: str, topic2: str) -> bool:
        """
        Check if two topics are related.

        Args:
            topic1: First topic
            topic2: Second topic

        Returns:
            True if topics are related
        """
        if not topic1 or not topic2:
            return False

        # Simple keyword matching (can be enhanced with NLP)
        topic1_words = set(topic1.lower().split())
        topic2_words = set(topic2.lower().split())
        
        # Check for common words
        common_words = topic1_words.intersection(topic2_words)
        
        # Also check if one topic contains the other
        topic1_lower = topic1.lower()
        topic2_lower = topic2.lower()
        
        return (len(common_words) > 0 or 
                topic1_lower in topic2_lower or 
                topic2_lower in topic1_lower)
