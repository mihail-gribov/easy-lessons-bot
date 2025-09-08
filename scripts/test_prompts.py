#!/usr/bin/env python3
"""Test script to demonstrate prompt store functionality."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.prompt_store import get_prompt_store
from core.session_state import SessionState


def main():
    """Demonstrate prompt store functionality."""
    print("=== Easy Lessons Bot - Prompt Store Demo ===\n")
    
    # Initialize prompt store
    prompt_store = get_prompt_store()
    print("✓ Prompt store initialized")
    
    # Create a test session
    session = SessionState(chat_id="demo_chat")
    session.set_topic("science")
    session.update_understanding_level("medium")
    session.add_message("user", "What is gravity?")
    session.add_message("bot", "Gravity is the force that pulls things down to Earth!")
    
    print(f"✓ Session created with topic: {session.active_topic}")
    print(f"✓ Understanding level: {session.understanding_level}")
    print(f"✓ History messages: {len(session.recent_messages)}")
    
    # Test context building
    user_message = "Why do things fall down?"
    messages = prompt_store.build_context(
        session=session,
        user_message=user_message,
        prompt_type="explanation"
    )
    
    print(f"\n✓ Built context with {len(messages)} messages")
    
    # Display context structure
    print("\n--- Context Structure ---")
    for i, msg in enumerate(messages):
        role = msg["role"]
        content_preview = msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"]
        print(f"{i+1}. {role.upper()}: {content_preview}")
    
    # Test available topics
    topics = prompt_store.get_available_topics()
    print(f"\n✓ Available topics ({len(topics)}): {', '.join(topics[:5])}...")
    
    # Test topic validation
    print(f"✓ 'math' is valid: {prompt_store.validate_topic('math')}")
    print(f"✓ 'invalid' is valid: {prompt_store.validate_topic('invalid')}")
    
    print("\n=== Demo completed successfully! ===")


if __name__ == "__main__":
    main()
