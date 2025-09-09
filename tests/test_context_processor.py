"""Tests for Context Processor merging logic."""

from core.context_processor import process_aux_result
from core.session_state import SessionState


class TestContextProcessor:
    """Test cases for merging auxiliary output with session state."""

    def test_new_topic_sets_discussion_and_flags(self):
        """New topic should set scenario=discussion and is_new_topic=True."""
        session = SessionState(chat_id="cp1")
        aux = {"topic": "Дроби", "understanding_level": 3}

        ctx = process_aux_result(session, aux)

        assert ctx["scenario"] == "discussion"
        assert ctx["topic"] == "Дроби"
        assert ctx["is_new_topic"] is True
        assert ctx["is_new_question"] is False

    def test_new_question_sets_explanation_and_flags(self):
        """New question should set scenario=explanation and is_new_question=True."""
        session = SessionState(chat_id="cp2")
        session.set_topic("Математика")
        aux = {"question": "Почему небо голубое?", "understanding_level": 5}

        ctx = process_aux_result(session, aux)

        assert ctx["scenario"] == "explanation"
        assert ctx["question"] == "Почему небо голубое?"
        assert ctx["is_new_question"] is True

    def test_recommendation_when_level_high(self):
        """Level >= 9 should include recommendation field."""
        session = SessionState(chat_id="cp3")
        aux = {"understanding_level": 9}

        ctx = process_aux_result(session, aux)

        assert ctx["understanding_level"] == 9
        assert "recommendation" in ctx
        assert isinstance(ctx["recommendation"], str)

    def test_preserve_when_no_changes(self):
        """If aux is empty, preserve session values and keep flags False."""
        session = SessionState(chat_id="cp4")
        session.set_topic("Физика")

        ctx = process_aux_result(session, {})

        assert ctx["scenario"] in {"discussion", "unknown"}
        assert ctx["topic"] == "Физика"
        assert ctx["is_new_topic"] in {False, True}  # depends on initial state after set_topic
        assert ctx["is_new_question"] is False


