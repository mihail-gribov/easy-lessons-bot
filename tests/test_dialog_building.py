"""Tests for building dialog context in PromptStore (two-model scheme)."""

from core.prompt_store import PromptStore
from core.session_state import SessionState


class TestDialogBuilding:
    def test_build_dialog_context_with_scenario_and_dynamic_block(self):
        store = PromptStore()
        session = SessionState(chat_id="db1")

        dynamic_ctx = {
            "scenario": "discussion",
            "topic": "Дроби",
            "question": None,
            "is_new_question": False,
            "is_new_topic": True,
            "understanding_level": 3,
            "previous_understanding_level": 2,
            "previous_topic": "Натуральные числа",
            "user_preferences": ["примеры", "мини-игры"],
        }

        messages = store.build_dialog_context(
            session, dynamic_ctx, "Начнем изучать дроби"
        )

        assert messages[0]["role"] == "system"
        content = messages[0]["content"]
        # Base + dynamic + scenario prompt must be stitched
        assert "Context:" in content
        assert "scenario" in content
        assert "Дроби" in content
        # Ensure user message is last
        assert messages[-1]["role"] == "user"
        assert "Начнем изучать дроби" in messages[-1]["content"]
