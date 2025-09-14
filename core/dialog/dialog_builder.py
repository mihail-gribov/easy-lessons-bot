"""Dialog builder for constructing LLM conversation contexts."""

import logging
from typing import Any

from core.session_state import SessionState

logger = logging.getLogger(__name__)


class DialogBuilder:
    """Builds dialog contexts for LLM requests."""

    def __init__(self, prompt_loader=None) -> None:
        """
        Initialize dialog builder.

        Args:
            prompt_loader: PromptLoader instance. If None, will be imported when needed.
        """
        self._prompt_loader = prompt_loader

    def _get_prompt_loader(self):
        """Get prompt loader instance."""
        if self._prompt_loader is None:
            from core.prompts.prompt_loader import PromptLoader
            self._prompt_loader = PromptLoader()
        return self._prompt_loader

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
        messages: list[dict[str, str]] = []

        # Add base system prompt and understanding context (legacy)
        prompt_loader = self._get_prompt_loader()
        base_prompt = prompt_loader.get_system_prompt("system_base")
        if not base_prompt:
            base_prompt = self._get_fallback_base_prompt()
            
        understanding_context = self._get_understanding_context(
            session.understanding_level, prompt_loader
        )
        system_prompt = f"{base_prompt}\n\n{understanding_context}"
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
            "Built legacy context for session %s: %d messages, topic=%s",
            session.chat_id,
            len(messages),
            session.active_topic,
        )

        return messages

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

        # Base system prompt with fallback
        prompt_loader = self._get_prompt_loader()
        base_prompt = prompt_loader.get_system_prompt("system_base")
        if not base_prompt:
            base_prompt = self._handle_prompt_loading_failure("system_base")

        # Dynamic context block
        dynamic_block = self._build_dynamic_context_block(dynamic_ctx)

        # Scenario prompt with fallback
        scenario_id = dynamic_ctx.get("scenario", "unknown")
        scenario_prompt = prompt_loader.get_scenario_prompt(scenario_id)
        if not scenario_prompt:
            scenario_prompt = self._handle_prompt_loading_failure(f"system_{scenario_id}")

        system_full = f"{base_prompt}\n\n{dynamic_block}\n\n{scenario_prompt}".strip()
        messages.append({"role": "system", "content": system_full})

        # History
        for msg in session.get_recent_messages(limit=30):
            role = "assistant" if msg.role == "bot" else msg.role
            messages.append({"role": role, "content": msg.content})

        # Current user message
        messages.append({"role": "user", "content": user_message})

        return messages

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

    def _get_understanding_context(
        self, level: int | str, prompt_loader
    ) -> str:
        """
        Get understanding level context.

        Args:
            level: Understanding level (0..9) or legacy label ('low'|'medium'|'high')
            prompt_loader: PromptLoader instance

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
        context = prompt_loader.get_system_prompt(prompt_key)
        if context:
            return context

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
        messages: list[dict[str, str]] = []
        recent_messages = session.get_recent_messages(limit=30)

        for msg in recent_messages:
            # Convert 'bot' role to 'assistant' for LLM compatibility
            role = "assistant" if msg.role == "bot" else msg.role
            messages.append(
                {
                    "role": role,
                    "content": msg.content,
                }
            )

        return messages

    def _get_fallback_base_prompt(self) -> str:
        """Get fallback base prompt."""
        return """You are a friendly and patient educational assistant for children aged 7-11. 
Your goal is to explain complex topics in simple, engaging language that children can understand.

Key principles:
- Use simple vocabulary and short sentences
- Respond in the child's language; use the language of their messages
- Provide real-life examples and analogies
- Ask engaging questions to check understanding
- Be encouraging and supportive
- Break down complex concepts into smaller parts
- Use visual descriptions when helpful

Always respond in a warm, encouraging tone that makes learning fun."""

    def _handle_prompt_loading_failure(self, prompt_name: str) -> str:
        """Handle prompt loading failure using graceful degradation."""
        from core.graceful_degradation import get_graceful_degradation_manager

        degradation_manager = get_graceful_degradation_manager()
        return degradation_manager.handle_prompt_loading_failure(prompt_name)
