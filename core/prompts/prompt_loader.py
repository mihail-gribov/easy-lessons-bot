"""Prompt loader for managing system prompts and scenario prompts."""

import logging
from pathlib import Path
from typing import Dict

logger = logging.getLogger(__name__)


class PromptLoader:
    """Handles loading of system prompts and scenario prompts from files."""

    def __init__(self, prompts_dir: Path | None = None) -> None:
        """
        Initialize prompt loader.

        Args:
            prompts_dir: Directory containing prompt files. If None, uses default location.
        """
        if prompts_dir is None:
            prompts_dir = Path(__file__).parent.parent / "prompts"
        
        self.prompts_dir = prompts_dir
        self._system_prompts: Dict[str, str] = {}
        self._scenario_prompts: Dict[str, str] = {}
        self._loaded = False

    def load_all_prompts(self) -> None:
        """Load all system and scenario prompts."""
        if self._loaded:
            return
            
        self._system_prompts = self._load_system_prompts()
        self._scenario_prompts = self._load_scenario_prompts()
        self._loaded = True

    def _load_system_prompts(self) -> Dict[str, str]:
        """
        Load system prompts from prompts directory.

        Returns:
            Dictionary of system prompts by name
        """
        prompts: Dict[str, str] = {}

        if not self.prompts_dir.exists():
            logger.warning("Prompts directory not found: %s", self.prompts_dir)
            return prompts

        # Load all .txt files from prompts directory (top-level only)
        for prompt_file in self.prompts_dir.glob("*.txt"):
            prompt_name = prompt_file.stem
            try:
                with open(prompt_file, encoding="utf-8") as f:
                    prompts[prompt_name] = f.read().strip()
                logger.debug("Loaded prompt: %s", prompt_name)
            except Exception as e:
                logger.error("Failed to load prompt %s: %s", prompt_name, e)

        # Fallback to built-in base prompt if file not found
        if "system_base" not in prompts:
            logger.warning("Base system prompt file not found, using built-in")
            prompts["system_base"] = self._get_base_system_prompt()

        return prompts

    def _load_scenario_prompts(self) -> Dict[str, str]:
        """
        Load scenario-specific system prompts from prompts/scenarios/ directory.

        Returns:
            Dictionary mapping scenario id to prompt text
        """
        prompts: Dict[str, str] = {}
        scenarios_dir = self.prompts_dir / "scenarios"

        if not scenarios_dir.exists():
            logger.warning("Scenario prompts directory not found: %s", scenarios_dir)
            return prompts

        for prompt_file in scenarios_dir.glob("system_*.txt"):
            scenario_id = prompt_file.stem.replace("system_", "")
            try:
                with open(prompt_file, encoding="utf-8") as f:
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
- Respond in the child's language; use the language of their messages
- Provide real-life examples and analogies
- Ask engaging questions to check understanding
- Be encouraging and supportive
- Break down complex concepts into smaller parts
- Use visual descriptions when helpful

Always respond in a warm, encouraging tone that makes learning fun."""

    def get_system_prompt(self, name: str) -> str | None:
        """
        Get system prompt by name.

        Args:
            name: Prompt name

        Returns:
            Prompt text or None if not found
        """
        if not self._loaded:
            self.load_all_prompts()
        return self._system_prompts.get(name)

    def get_scenario_prompt(self, scenario_id: str) -> str | None:
        """
        Get scenario prompt by ID.

        Args:
            scenario_id: Scenario identifier

        Returns:
            Prompt text or None if not found
        """
        if not self._loaded:
            self.load_all_prompts()
        return self._scenario_prompts.get(scenario_id)

    def get_all_system_prompts(self) -> Dict[str, str]:
        """
        Get all system prompts.

        Returns:
            Dictionary of all system prompts
        """
        if not self._loaded:
            self.load_all_prompts()
        return self._system_prompts.copy()

    def get_all_scenario_prompts(self) -> Dict[str, str]:
        """
        Get all scenario prompts.

        Returns:
            Dictionary of all scenario prompts
        """
        if not self._loaded:
            self.load_all_prompts()
        return self._scenario_prompts.copy()

    def reload_prompts(self) -> None:
        """Reload all prompts from files."""
        self._loaded = False
        self._system_prompts.clear()
        self._scenario_prompts.clear()
        self.load_all_prompts()
