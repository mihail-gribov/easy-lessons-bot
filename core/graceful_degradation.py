"""Graceful degradation mechanisms for handling partial system failures."""

import logging
from typing import Any

from core.session_state import SessionState

logger = logging.getLogger(__name__)


class GracefulDegradationManager:
    """Manages graceful degradation when system components fail."""

    def __init__(self) -> None:
        """Initialize graceful degradation manager."""
        self._fallback_responses = [
            "Интересный вопрос! Давай подумаем об этом вместе.",
            "Хм, это хорошая тема для обсуждения!",
            "Отличный вопрос! Что ты думаешь об этом?",
            "Давай разберем это пошагово.",
            "Это важная тема! Расскажи, что ты уже знаешь об этом?",
        ]

    def handle_auxiliary_model_failure(
        self,
        session: SessionState,
        user_message: str,
    ) -> dict[str, Any]:
        """
        Handle auxiliary model failure by providing fallback context.

        Args:
            session: Current session state
            user_message: User's message

        Returns:
            Fallback dynamic context
        """
        logger.warning("Auxiliary model failed, using fallback context")

        # Simple heuristics for fallback context
        is_new_topic = self._detect_new_topic_heuristic(session, user_message)
        is_new_question = self._detect_new_question_heuristic(session, user_message)

        # Determine scenario based on heuristics
        if is_new_topic:
            scenario = "discussion"
        elif is_new_question:
            scenario = "explanation"
        else:
            scenario = "unknown"

        return {
            "scenario": scenario,
            "topic": session.topic,
            "question": session.question,
            "is_new_question": is_new_question,
            "is_new_topic": is_new_topic,
            "understanding_level": session.understanding_level,
            "previous_understanding_level": session.previous_understanding_level,
            "previous_topic": session.previous_topic,
            "user_preferences": session.user_preferences,
        }

    def handle_dialog_model_failure(
        self,
        session: SessionState,
        user_message: str,
    ) -> str:
        """
        Handle dialog model failure by providing fallback response.

        Args:
            session: Current session state
            user_message: User's message

        Returns:
            Fallback response text
        """
        logger.warning("Dialog model failed, using fallback response")

        # Try to provide context-aware fallback
        if session.topic:
            return f"Отличный вопрос о {session.topic}! Давай обсудим это подробнее. Что именно тебя интересует?"

        # Generic fallback
        import random

        return random.choice(self._fallback_responses)

    def handle_prompt_loading_failure(self, prompt_name: str) -> str:
        """
        Handle prompt loading failure by providing fallback prompt.

        Args:
            prompt_name: Name of the failed prompt

        Returns:
            Fallback prompt text
        """
        logger.warning("Failed to load prompt %s, using fallback", prompt_name)

        fallback_prompts = {
            "system_base": (
                "You are a friendly educational assistant for children aged 7-11. "
                "Explain things simply and encourage learning."
            ),
            "system_discussion": (
                "Help the child explore and discuss the topic. "
                "Ask questions and encourage their thoughts."
            ),
            "system_explanation": (
                "Provide clear, simple explanations with examples. "
                "Check understanding and ask follow-up questions."
            ),
            "system_unknown": (
                "Be helpful and friendly. Ask clarifying questions "
                "to understand what the child needs."
            ),
        }

        return fallback_prompts.get(prompt_name, "Be helpful and friendly.")

    def _detect_new_topic_heuristic(
        self, session: SessionState, user_message: str
    ) -> bool:
        """Simple heuristic to detect new topic mentions."""
        if not session.topic:
            return True

        # Look for topic change indicators
        topic_indicators = [
            "новая тема",
            "другая тема",
            "сменим тему",
            "давай о",
            "расскажи о",
            "что такое",
            "объясни что такое",
        ]

        message_lower = user_message.lower()
        return any(indicator in message_lower for indicator in topic_indicators)

    def _detect_new_question_heuristic(
        self, session: SessionState, user_message: str
    ) -> bool:
        """Simple heuristic to detect new questions."""
        question_indicators = ["?", "как", "что", "почему", "зачем", "когда", "где"]
        message_lower = user_message.lower()

        # Check for question marks or question words
        has_question_mark = "?" in user_message
        has_question_word = any(word in message_lower for word in question_indicators)

        return has_question_mark or has_question_word


# Global graceful degradation manager instance
_graceful_degradation_manager: GracefulDegradationManager | None = None


def get_graceful_degradation_manager() -> GracefulDegradationManager:
    """Get global graceful degradation manager instance."""
    global _graceful_degradation_manager  # noqa: PLW0603
    if _graceful_degradation_manager is None:
        _graceful_degradation_manager = GracefulDegradationManager()
    return _graceful_degradation_manager
