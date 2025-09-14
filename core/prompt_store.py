"""Prompt store for managing system prompts and context building."""

import logging
from typing import Any

from core.context.context_analyzer import ContextAnalyzer
from core.dialog.dialog_builder import DialogBuilder
from core.prompts.prompt_loader import PromptLoader
from core.session_state import SessionState

logger = logging.getLogger(__name__)


class PromptStore:
    """Manages system prompts and builds context for LLM requests."""

    def __init__(self, prompt_loader=None, context_analyzer=None, dialog_builder=None) -> None:
        """
        Initialize prompt store.
        
        Args:
            prompt_loader: PromptLoader instance. If None, gets from DI container.
            context_analyzer: ContextAnalyzer instance. If None, gets from DI container.
            dialog_builder: DialogBuilder instance. If None, gets from DI container.
        """
        if prompt_loader is None:
            try:
                from core.service_registry import get_prompt_loader
                self._prompt_loader = get_prompt_loader()
            except Exception:
                self._prompt_loader = PromptLoader()
        else:
            self._prompt_loader = prompt_loader
            
        if context_analyzer is None:
            try:
                from core.service_registry import get_context_analyzer
                self._context_analyzer = get_context_analyzer()
            except Exception:
                self._context_analyzer = ContextAnalyzer()
        else:
            self._context_analyzer = context_analyzer
            
        if dialog_builder is None:
            try:
                from core.service_registry import get_dialog_builder
                self._dialog_builder = get_dialog_builder()
            except Exception:
                self._dialog_builder = DialogBuilder(self._prompt_loader)
        else:
            self._dialog_builder = dialog_builder


    def build_context(
        self,
        session: SessionState,
        user_message: str,
        prompt_type: str = "explanation",
    ) -> list[dict[str, str]]:
        """
        Build context for LLM request (legacy single-model path).

        Args:
            session: User session state
            user_message: Current user message
            prompt_type: Type of prompt (kept for backward compatibility)

        Returns:
            List of messages for LLM request
        """
        return self._dialog_builder.build_context(session, user_message, prompt_type)


    async def analyze_context_with_auxiliary_model(
        self,
        session: SessionState,
        user_message: str,
    ) -> dict[str, Any]:
        """
        Analyze last 5 messages and current context using auxiliary model.

        Returns a dict with keys: scenario, topic, question, is_new_question, is_new_topic,
        understanding_level, previous_understanding_level, previous_topic, user_preferences.
        """
        return await self._context_analyzer.analyze_context_with_auxiliary_model(
            session, user_message
        )

    def build_dialog_context(
        self,
        session: SessionState,
        dynamic_ctx: dict[str, Any],
        user_message: str,
    ) -> list[dict[str, str]]:
        """
        Build messages for dialog model: system (base + dynamic + scenario), history, user.
        System prompt must be the first and never truncated.
        """
        return self._dialog_builder.build_dialog_context(session, dynamic_ctx, user_message)


    def get_available_topics(self) -> list[str]:
        """
        Get list of available topics.

        Returns:
            List of topic names
        """
        # For MVP, return a basic list of common educational topics
        return [
            "math",
            "science",
            "reading",
            "writing",
            "history",
            "geography",
            "art",
            "music",
            "sports",
            "nature",
            "animals",
            "space",
            "technology",
            "cooking",
            "gardening",
        ]

    def validate_topic(self, topic: str) -> bool:
        """
        Validate if topic is supported.

        Args:
            topic: Topic name to validate

        Returns:
            True if topic is valid
        """
        available_topics = self.get_available_topics()
        return topic.lower() in [t.lower() for t in available_topics]

    async def identify_topic_with_llm(
        self,
        session: SessionState,
        user_message: str,
    ) -> str:
        """
        Legacy topic identification kept for compatibility in tests.
        Always validates against available topics and returns 'unknown' if not matched.
        """
        available_topics = self.get_available_topics()
        return await self._context_analyzer.identify_topic_with_llm(
            session, user_message, available_topics
        )

    def _get_topic_identification_fallback(self) -> str:
        """Deprecated: retained for tests that may import it. Returns minimal text."""
        return "You are a topic identification assistant. Return ONLY one word from the allowed list."


# Global prompt store instance
_prompt_store: PromptStore | None = None


def get_prompt_store() -> PromptStore:
    """Get global prompt store instance."""
    global _prompt_store  # noqa: PLW0603
    if _prompt_store is None:
        _prompt_store = PromptStore()
    return _prompt_store
