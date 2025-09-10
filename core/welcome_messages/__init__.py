"""Welcome messages store with random selection."""

from __future__ import annotations

import random
from pathlib import Path


def get_random_welcome_message() -> str:
    """Load a random welcome message from core/welcome_messages/*.txt."""
    base_dir = Path(__file__).parent
    files = sorted(base_dir.glob("*.txt"))
    if not files:
        # Fallback simple welcome text (no emojis per user preference)
        return (
            "Привет! Я Easy Lessons Bot и я здесь, чтобы помочь тебе разобраться в любой теме простыми словами! "
            "Я объясняю сложные вещи так, чтобы тебе было понятно и интересно. "
            "Ты можешь задать мне любой вопрос или выбрать интересную тему для обсуждения. "
            "Напиши, что хочешь изучить, и мы начнем наше увлекательное путешествие в мир знаний!"
        )
    chosen = random.choice(files)
    try:
        return chosen.read_text(encoding="utf-8").strip()
    except Exception:
        return (
            "Привет! Я Easy Lessons Bot и я здесь, чтобы помочь тебе разобраться в любой теме простыми словами! "
            "Я объясняю сложные вещи так, чтобы тебе было понятно и интересно. "
            "Ты можешь задать мне любой вопрос или выбрать интересную тему для обсуждения. "
            "Напиши, что хочешь изучить, и мы начнем наше увлекательное путешествие в мир знаний!"
        )
