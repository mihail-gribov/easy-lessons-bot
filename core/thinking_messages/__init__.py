"""Thinking messages store with random selection."""

from __future__ import annotations

import random
from pathlib import Path


def get_random_thinking_message() -> str:
    """Load a random thinking message from core/thinking_messages/*.txt."""
    base_dir = Path(__file__).parent
    files = sorted(base_dir.glob("*.txt"))
    if not files:
        # Fallback simple thinking text
        return "минуточку, я подумаю..."
    
    chosen = random.choice(files)
    try:
        return chosen.read_text(encoding="utf-8").strip()
    except Exception:
        return "минуточку, я подумаю..."

