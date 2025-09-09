"""Context Processor merges auxiliary model output with session context."""

from __future__ import annotations

from typing import Any, Dict

from core.session_state import SessionState


def _normalize_scenario(s: str | None) -> str:
    """Normalize scenario identifier to one of: discussion|explanation|unknown."""
    if not s:
        return "unknown"
    s_lower = s.strip().lower()
    mapping: dict[str, str] = {
        "discussion": "discussion",
        "topic": "discussion",
        "talk": "discussion",
        "explanation": "explanation",
        "question": "explanation",
        "qa": "explanation",
        "unknown": "unknown",
        "other": "unknown",
    }
    return mapping.get(s_lower, "unknown")


def process_aux_result(session: SessionState, aux: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge auxiliary model result with session state to produce dynamic context.

    Rules are based on doc/dialog_flow.md (Context Processor section):
    - If a new question is detected → set question, set is_new_question=True, scenario=explanation
    - If a new topic is detected → set topic, set is_new_topic=True, scenario=discussion
    - Preserve previous values if not provided by auxiliary output
    - Maintain previous_understanding_level from session
    - If understanding_level >= 9 → add recommendation to finish topic/question
    """

    # Start with current session context
    scenario = _normalize_scenario(aux.get("scenario")) or session.scenario

    # Initialize defaults
    topic = session.topic
    question = session.question
    is_new_topic = False
    is_new_question = False

    # Handle topic
    aux_topic = aux.get("topic")
    if isinstance(aux_topic, str) and aux_topic.strip():
        if aux_topic != session.topic:
            topic = aux_topic
            is_new_topic = True
            scenario = "discussion"

    # Handle question
    aux_question = aux.get("question")
    if isinstance(aux_question, str) and aux_question.strip():
        if aux_question != session.question:
            question = aux_question
            is_new_question = True
            scenario = "explanation"

    # Understanding level
    previous_understanding_level = session.understanding_level
    understanding_level = aux.get("understanding_level", session.understanding_level)
    try:
        understanding_level_int = int(understanding_level)
    except Exception:
        understanding_level_int = session.understanding_level

    # User preferences (list[str])
    user_preferences: list[str] = []
    aux_prefs = aux.get("user_preferences")
    if isinstance(aux_prefs, list):
        user_preferences = [str(x) for x in aux_prefs if isinstance(x, (str, int, float))]

    # Previous topic
    previous_topic = session.previous_topic if session.previous_topic else None
    if is_new_topic and session.topic and session.topic != topic:
        previous_topic = session.topic

    # Recommendation if level >= 9
    recommendation: str | None = None
    if understanding_level_int >= 9:
        recommendation = "Consider wrapping up the current topic/question and move to a new one."

    # Update session with merged context
    session.scenario = scenario
    session.topic = topic
    session.question = question
    session.is_new_topic = is_new_topic
    session.is_new_question = is_new_question
    session.previous_understanding_level = previous_understanding_level
    session.update_understanding_level(understanding_level_int)
    session.previous_topic = previous_topic
    session.user_preferences = user_preferences

    # Compose dynamic context dict
    dynamic_context: Dict[str, Any] = {
        "scenario": scenario,
        "question": question,
        "topic": topic,
        "is_new_question": is_new_question,
        "is_new_topic": is_new_topic,
        "understanding_level": session.understanding_level,
        "previous_understanding_level": previous_understanding_level,
        "previous_topic": previous_topic,
        "user_preferences": user_preferences,
    }

    if recommendation:
        dynamic_context["recommendation"] = recommendation

    return dynamic_context


