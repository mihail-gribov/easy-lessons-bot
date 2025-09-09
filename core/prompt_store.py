"""Prompt store for managing system prompts and context building."""

import logging
import json
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
        self._scenario_prompts = self._load_scenario_prompts()

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

    def _load_scenario_prompts(self) -> dict[str, str]:
        """
        Load scenario-specific system prompts from core/prompts/scenarios/.

        Returns:
            Dictionary mapping scenario id to prompt text
        """
        prompts: dict[str, str] = {}
        scenarios_dir = Path(__file__).parent / "prompts" / "scenarios"

        if not scenarios_dir.exists():
            logger.warning("Scenario prompts directory not found: %s", scenarios_dir)
            return prompts

        for prompt_file in scenarios_dir.glob("system_*.txt"):
            scenario_id = prompt_file.stem.replace("system_", "")
            try:
                with open(prompt_file, "r", encoding="utf-8") as f:
                    prompts[scenario_id] = f.read().strip()
                logger.debug("Loaded scenario prompt: %s", scenario_id)
            except Exception as e:
                logger.error("Failed to load scenario prompt %s: %s", scenario_id, e)

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

    def _build_dynamic_context_block(self, dynamic_ctx: dict[str, Any]) -> str:
        """Serialize dynamic context into a compact, readable block."""
        lines: list[str] = ["Context:"]
        order = [
            "scenario",
            "topic",
            "question",
            "is_new_question",
            "is_new_topic",
            "understanding_level",
            "previous_understanding_level",
            "previous_topic",
            "user_preferences",
            "recommendation",
        ]
        for key in order:
            if key in dynamic_ctx and dynamic_ctx[key] is not None:
                value = dynamic_ctx[key]
                if isinstance(value, list):
                    value_str = ", ".join(str(v) for v in value)
                else:
                    value_str = str(value)
                lines.append(f"- {key}: {value_str}")
        return "\n".join(lines)

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
        from core.llm_client import get_llm_client  # import here to avoid cycles

        llm_client = get_llm_client()

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

        response = await llm_client.generate_response(
            messages=messages,
            temperature=0.1,
            max_tokens=200,
        )

        try:
            data = json.loads(response)
            if not isinstance(data, dict):
                raise ValueError("Auxiliary model did not return a JSON object")
        except Exception:
            # Fallback minimal context
            data = {
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

        return data

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
        messages: list[dict[str, str]] = []

        # Base system prompt
        base_prompt = self._system_prompts.get("system_base", self._get_base_system_prompt())

        # Dynamic context block
        dynamic_block = self._build_dynamic_context_block(dynamic_ctx)

        # Scenario prompt
        scenario_id = dynamic_ctx.get("scenario", "unknown")
        scenario_prompt = self._scenario_prompts.get(scenario_id, "")

        system_full = f"{base_prompt}\n\n{dynamic_block}\n\n{scenario_prompt}".strip()
        messages.append({"role": "system", "content": system_full})

        # History
        for msg in session.get_recent_messages(limit=30):
            role = "assistant" if msg.role == "bot" else msg.role
            messages.append({"role": role, "content": msg.content})

        # Current user message
        messages.append({"role": "user", "content": user_message})

        return messages

    def _get_understanding_context(self, level: int | str) -> str:
        """
        Get understanding level context.

        Args:
            level: Understanding level (0..9) or legacy label ('low'|'medium'|'high')

        Returns:
            Understanding context text
        """
        # Normalize to legacy label for backward compatibility
        if isinstance(level, int):
            if level <= 2:
                label = "low"
            elif level <= 6:
                label = "medium"
            else:
                label = "high"
        else:
            label = level.lower()

        # Try to load from prompts first by label
        prompt_key = f"understanding_{label}"
        if prompt_key in self._system_prompts:
            return self._system_prompts[prompt_key]

        # Fallback to built-in contexts
        contexts = {
            "low": "The child is just starting to learn this topic. Use very simple language, lots of examples, and check understanding frequently.",
            "medium": "The child has some basic understanding. You can use slightly more complex explanations and build on their existing knowledge.",
            "high": "The child has good understanding. You can use more detailed explanations and introduce related concepts.",
        }
        return contexts.get(label, contexts["medium"])

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
            # Convert 'bot' role to 'assistant' for LLM compatibility
            role = "assistant" if msg.role == "bot" else msg.role
            messages.append({
                "role": role,
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

    async def identify_topic_with_llm(
        self, 
        session: SessionState, 
        user_message: str
    ) -> str:
        """
        Use LLM to identify topic from conversation context.
        
        Args:
            session: User session state with message history
            user_message: Current user message
            
        Returns:
            Topic name from available topics or "unknown"
        """
        try:
            # Import here to avoid circular imports
            from core.llm_client import get_llm_client
            
            # Get LLM client
            llm_client = get_llm_client()
            
            # Build context with last 5 messages
            messages = []
            
            # Add system prompt for topic identification
            topic_prompt = self._system_prompts.get("topic_identification", "")
            if not topic_prompt:
                logger.warning("Topic identification prompt not found, using fallback")
                topic_prompt = self._get_topic_identification_fallback()
            
            messages.append({"role": "system", "content": topic_prompt})
            
            # Add conversation history (last 5 messages)
            recent_messages = session.get_recent_messages(limit=5)
            for msg in recent_messages:
                # Convert 'bot' role to 'assistant' for LLM compatibility
                role = "assistant" if msg.role == "bot" else msg.role
                messages.append({
                    "role": role,
                    "content": msg.content,
                })
            
            # Add current user message
            messages.append({"role": "user", "content": user_message})
            
            logger.debug(
                "Sending topic identification request for session %s: %d messages",
                session.chat_id,
                len(messages)
            )
            
            # Send request to LLM with short timeout and low temperature
            response = await llm_client.generate_response(
                messages=messages,
                temperature=0.1,  # Low temperature for accuracy
                max_tokens=50,    # Short response
            )
            
            # Clean and validate response
            topic = response.strip().lower()
            
            # Validate against available topics
            if self.validate_topic(topic):
                logger.info(
                    "LLM identified topic for session %s: %s",
                    session.chat_id,
                    topic
                )
                return topic
            else:
                logger.info(
                    "LLM returned unknown topic for session %s: %s",
                    session.chat_id,
                    topic
                )
                return "unknown"
                
        except Exception as e:
            logger.exception("Error in topic identification for session %s", session.chat_id)
            return "unknown"

    def _get_topic_identification_fallback(self) -> str:
        """Get fallback topic identification prompt if file not found."""
        return """You are a topic identification assistant. Your ONLY task is to return one of these exact topic names:

math, science, reading, writing, history, geography, art, music, sports, nature, animals, space, technology, cooking, gardening, unknown

RULES:
1. Return ONLY one word from the list above
2. If the user wants to learn about mathematics, numbers, fractions, algebra, geometry → return "math"
3. If the user wants to learn about physics, chemistry, biology, experiments → return "science"
4. If the user wants to learn about books, stories, literature → return "reading"
5. If the user wants to learn about writing, grammar, composition → return "writing"
6. If the user wants to learn about past events, historical figures → return "history"
7. If the user wants to learn about countries, maps, places → return "geography"
8. If the user wants to learn about drawing, painting, creativity → return "art"
9. If the user wants to learn about songs, instruments, music theory → return "music"
10. If the user wants to learn about physical activities, games → return "sports"
11. If the user wants to learn about plants, environment, ecology → return "nature"
12. If the user wants to learn about animals, wildlife, pets → return "animals"
13. If the user wants to learn about planets, stars, universe → return "space"
14. If the user wants to learn about computers, programming, gadgets → return "technology"
15. If the user wants to learn about food preparation, recipes → return "cooking"
16. If the user wants to learn about growing plants, gardening → return "gardening"
17. If the request doesn't match any topic above → return "unknown"

RESPONSE FORMAT: Return only one word from the list. No explanations, no additional text."""


# Global prompt store instance
_prompt_store: PromptStore | None = None


def get_prompt_store() -> PromptStore:
    """Get global prompt store instance."""
    global _prompt_store  # noqa: PLW0603
    if _prompt_store is None:
        _prompt_store = PromptStore()
    return _prompt_store
