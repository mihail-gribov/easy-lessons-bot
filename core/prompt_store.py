"""Prompt store for managing system prompts and context building."""

import logging
import os
from pathlib import Path
from typing import Any

from core.session_state import Message, SessionState

logger = logging.getLogger(__name__)


class PromptStore:
    """Manages system prompts and builds context for LLM requests."""

    def __init__(self) -> None:
        """Initialize prompt store."""
        self._system_prompts = self._load_system_prompts()

    def _load_system_prompts(self) -> dict[str, str]:
        """
        Load system prompts from core/prompts/ directory.

        Returns:
            Dictionary of system prompts by name
        """
        prompts = {}
        prompts_dir = Path(__file__).parent / "prompts"
        
        # Load all .txt files from prompts directory
        for prompt_file in prompts_dir.glob("*.txt"):
            prompt_name = prompt_file.stem
            try:
                with open(prompt_file, "r", encoding="utf-8") as f:
                    prompts[prompt_name] = f.read().strip()
                logger.debug("Loaded prompt: %s", prompt_name)
            except Exception as e:
                logger.error("Failed to load prompt %s: %s", prompt_name, e)
        
        # Fallback to built-in prompts if files not found
        if not prompts:
            logger.warning("No prompt files found, using built-in prompts")
            prompts = {
                "system_base": self._get_base_system_prompt(),
                "system_explanation": self._get_explanation_prompt(),
                "system_question": self._get_question_prompt(),
            }
        
        return prompts

    def _get_base_system_prompt(self) -> str:
        """Get base system prompt."""
        return """You are a friendly and patient educational assistant for children aged 7-11. 
Your goal is to explain complex topics in simple, engaging language that children can understand.

Key principles:
- Use simple vocabulary and short sentences
- Provide real-life examples and analogies
- Ask engaging questions to check understanding
- Be encouraging and supportive
- Break down complex concepts into smaller parts
- Use visual descriptions when helpful

Always respond in a warm, encouraging tone that makes learning fun."""

    def _get_explanation_prompt(self) -> str:
        """Get explanation-focused system prompt."""
        return """You are explaining a topic to a child. Focus on:
- Clear, simple explanations with examples
- Connecting new concepts to things they already know
- Using analogies and comparisons
- Asking questions to check their understanding
- Encouraging them to ask more questions

Make the explanation engaging and interactive."""

    def _get_question_prompt(self) -> str:
        """Get question-answering system prompt."""
        return """A child has asked you a question. Your response should:
- Answer their question directly and simply
- Provide additional context if helpful
- Ask a follow-up question to deepen their understanding
- Encourage them to explore the topic further
- Use examples they can relate to

Be patient and thorough in your explanation."""

    def build_context(
        self,
        session: SessionState,
        user_message: str,
        prompt_type: str = "explanation",
    ) -> list[dict[str, str]]:
        """
        Build context for LLM request.

        Args:
            session: User session state
            user_message: Current user message
            prompt_type: Type of prompt ('explanation' or 'question')

        Returns:
            List of messages for LLM request
        """
        messages = []

        # Add system prompt
        system_prompt = self._get_system_prompt(session, prompt_type)
        messages.append({"role": "system", "content": system_prompt})

        # Add topic context if available
        if session.active_topic:
            topic_context = self._build_topic_context(session.active_topic)
            messages.append({"role": "system", "content": topic_context})

        # Add conversation history
        history_messages = self._build_history_context(session)
        messages.extend(history_messages)

        # Add current user message
        messages.append({"role": "user", "content": user_message})

        logger.debug(
            "Built context for session %s: %d messages, topic=%s, type=%s",
            session.chat_id,
            len(messages),
            session.active_topic,
            prompt_type,
        )

        return messages

    def _get_system_prompt(self, session: SessionState, prompt_type: str) -> str:
        """
        Get system prompt based on session and type.

        Args:
            session: User session state
            prompt_type: Type of prompt

        Returns:
            System prompt text
        """
        base_prompt = self._system_prompts["system_base"]
        
        # Add understanding level context
        understanding_context = self._get_understanding_context(session.understanding_level)
        
        # Add specific prompt type
        if prompt_type == "explanation":
            type_prompt = self._system_prompts["system_explanation"]
        elif prompt_type == "question":
            type_prompt = self._system_prompts["system_question"]
        else:
            type_prompt = self._system_prompts["system_explanation"]

        return f"{base_prompt}\n\n{understanding_context}\n\n{type_prompt}"

    def _get_understanding_context(self, level: str) -> str:
        """
        Get understanding level context.

        Args:
            level: Understanding level ('low', 'medium', 'high')

        Returns:
            Understanding context text
        """
        # Try to load from prompts first
        prompt_key = f"understanding_{level}"
        if prompt_key in self._system_prompts:
            return self._system_prompts[prompt_key]
        
        # Fallback to built-in contexts
        contexts = {
            "low": "The child is just starting to learn this topic. Use very simple language, lots of examples, and check understanding frequently.",
            "medium": "The child has some basic understanding. You can use slightly more complex explanations and build on their existing knowledge.",
            "high": "The child has good understanding. You can use more detailed explanations and introduce related concepts.",
        }
        return contexts.get(level, contexts["medium"])

    def _build_topic_context(self, topic: str) -> str:
        """
        Build topic-specific context.

        Args:
            topic: Active topic name

        Returns:
            Topic context text
        """
        return f"Current topic: {topic}. Focus your explanations and examples on this topic. If the user asks about something else, gently guide them back to this topic or ask if they want to start a new topic."

    def _build_history_context(self, session: SessionState) -> list[dict[str, str]]:
        """
        Build conversation history context.

        Args:
            session: User session state

        Returns:
            List of historical messages
        """
        messages = []
        recent_messages = session.get_recent_messages(limit=30)

        for msg in recent_messages:
            messages.append({
                "role": msg.role,
                "content": msg.content,
            })

        return messages

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


# Global prompt store instance
_prompt_store: PromptStore | None = None


def get_prompt_store() -> PromptStore:
    """Get global prompt store instance."""
    global _prompt_store  # noqa: PLW0603
    if _prompt_store is None:
        _prompt_store = PromptStore()
    return _prompt_store
