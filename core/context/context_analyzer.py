"""Context analyzer for analyzing conversation context using auxiliary model."""

import json
import logging
from typing import Any

from core.session_state import SessionState

logger = logging.getLogger(__name__)


class ContextAnalyzer:
    """Analyzes conversation context using auxiliary model."""

    def __init__(self, llm_client=None) -> None:
        """
        Initialize context analyzer.

        Args:
            llm_client: LLM client instance. If None, will be imported when needed.
        """
        self._llm_client = llm_client

    def _get_llm_client(self):
        """Get LLM client instance."""
        if self._llm_client is None:
            from core.llm_client import get_llm_client
            self._llm_client = get_llm_client()
        return self._llm_client

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
        llm_client = self._get_llm_client()

        system_prompt = (
            "You are an assistant that extracts dialog control parameters. "
            "Given recent conversation and the latest user message, return a strict JSON object with keys: "
            "scenario (one of: discussion, explanation, unknown), topic (string|null), question (string|null), "
            "is_new_question (boolean), is_new_topic (boolean), understanding_level (integer 0-9), "
            "previous_understanding_level (integer|null), previous_topic (string|null), user_preferences (array of strings). "
            "If unsure, prefer unknown/null and false flags. Do not add extra keys or text."
        )

        messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]

        # Add last 5 messages from history
        for msg in session.get_recent_messages(limit=5):
            role = "assistant" if msg.role == "bot" else msg.role
            messages.append({"role": role, "content": msg.content})

        # Add current user message last
        messages.append({"role": "user", "content": user_message})

        try:
            response = await llm_client.generate_response(
                messages=messages,
                temperature=0.1,
                max_tokens=200,
            )

            try:
                data = json.loads(response)
                if not isinstance(data, dict):
                    raise ValueError("Auxiliary model did not return a JSON object")
            except Exception as e:
                logger.warning("Failed to parse auxiliary model response: %s", e)
                # Fallback minimal context
                data = self._get_fallback_context(session)

        except Exception as e:
            logger.warning("Auxiliary model failed: %s", e)
            # Use graceful degradation
            data = await self._handle_auxiliary_model_failure(session, user_message)

        return data

    def _get_fallback_context(self, session: SessionState) -> dict[str, Any]:
        """Get fallback context when auxiliary model fails."""
        return {
            "scenario": "unknown",
            "topic": session.topic,
            "question": None,
            "is_new_question": False,
            "is_new_topic": False,
            "understanding_level": session.understanding_level,
            "previous_understanding_level": session.previous_understanding_level,
            "previous_topic": session.previous_topic,
            "user_preferences": session.user_preferences,
        }

    async def _handle_auxiliary_model_failure(
        self, session: SessionState, user_message: str
    ) -> dict[str, Any]:
        """Handle auxiliary model failure using graceful degradation."""
        from core.graceful_degradation import get_graceful_degradation_manager

        degradation_manager = get_graceful_degradation_manager()
        return degradation_manager.handle_auxiliary_model_failure(session, user_message)

    async def identify_topic_with_llm(
        self,
        session: SessionState,
        user_message: str,
        available_topics: list[str],
    ) -> str:
        """
        Identify topic using LLM.

        Args:
            session: User session state
            user_message: Current user message
            available_topics: List of available topics

        Returns:
            Identified topic or 'unknown' if not found
        """
        try:
            llm_client = self._get_llm_client()

            messages: list[dict[str, str]] = []

            # Minimal system instruction without external file
            topic_prompt = (
                "You are a topic identification assistant. Return ONLY one word from this list: "
                f"{', '.join(available_topics)}, unknown."
            )
            messages.append({"role": "system", "content": topic_prompt})

            # Add last 5 messages
            for msg in session.get_recent_messages(limit=5):
                role = "assistant" if msg.role == "bot" else msg.role
                messages.append({"role": role, "content": msg.content})

            # Add current user message
            messages.append({"role": "user", "content": user_message})

            response = await llm_client.generate_response(
                messages=messages,
                temperature=0.1,
                max_tokens=50,
            )

            topic = response.strip().lower()
            if topic in available_topics:
                return topic
            return "unknown"
        except Exception:
            return "unknown"
