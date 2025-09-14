"""Tests for PromptLoader class."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from core.prompts.prompt_loader import PromptLoader


class TestPromptLoader:
    """Test cases for PromptLoader."""

    def test_prompt_loader_initialization(self):
        """Test PromptLoader initialization with default directory."""
        loader = PromptLoader()
        assert loader.prompts_dir is not None
        assert isinstance(loader.prompts_dir, Path)

    def test_prompt_loader_initialization_with_custom_dir(self):
        """Test PromptLoader initialization with custom directory."""
        custom_dir = Path("/custom/prompts")
        loader = PromptLoader(custom_dir)
        assert loader.prompts_dir == custom_dir

    def test_load_system_prompts_empty_directory(self):
        """Test loading system prompts from empty directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            loader = PromptLoader(Path(temp_dir))
            prompts = loader._load_system_prompts()
            assert isinstance(prompts, dict)
            assert "system_base" in prompts  # Should have fallback

    def test_load_system_prompts_with_files(self):
        """Test loading system prompts from directory with files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test prompt files
            (temp_path / "system_base.txt").write_text("Base system prompt")
            (temp_path / "understanding_low.txt").write_text("Low understanding prompt")
            
            loader = PromptLoader(temp_path)
            prompts = loader._load_system_prompts()
            
            assert "system_base" in prompts
            assert "understanding_low" in prompts
            assert prompts["system_base"] == "Base system prompt"
            assert prompts["understanding_low"] == "Low understanding prompt"

    def test_load_scenario_prompts_empty_directory(self):
        """Test loading scenario prompts from empty directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            loader = PromptLoader(Path(temp_dir))
            prompts = loader._load_scenario_prompts()
            assert isinstance(prompts, dict)
            assert len(prompts) == 0

    def test_load_scenario_prompts_with_files(self):
        """Test loading scenario prompts from directory with files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            scenarios_dir = temp_path / "scenarios"
            scenarios_dir.mkdir()
            
            # Create test scenario files
            (scenarios_dir / "system_discussion.txt").write_text("Discussion prompt")
            (scenarios_dir / "system_explanation.txt").write_text("Explanation prompt")
            
            loader = PromptLoader(temp_path)
            prompts = loader._load_scenario_prompts()
            
            assert "discussion" in prompts
            assert "explanation" in prompts
            assert prompts["discussion"] == "Discussion prompt"
            assert prompts["explanation"] == "Explanation prompt"

    def test_get_system_prompt_existing(self):
        """Test getting existing system prompt."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            (temp_path / "test_prompt.txt").write_text("Test prompt content")
            
            loader = PromptLoader(temp_path)
            prompt = loader.get_system_prompt("test_prompt")
            
            assert prompt == "Test prompt content"

    def test_get_system_prompt_nonexistent(self):
        """Test getting non-existent system prompt."""
        with tempfile.TemporaryDirectory() as temp_dir:
            loader = PromptLoader(Path(temp_dir))
            prompt = loader.get_system_prompt("nonexistent")
            
            assert prompt is None

    def test_get_scenario_prompt_existing(self):
        """Test getting existing scenario prompt."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            scenarios_dir = temp_path / "scenarios"
            scenarios_dir.mkdir()
            (scenarios_dir / "system_test.txt").write_text("Test scenario")
            
            loader = PromptLoader(temp_path)
            prompt = loader.get_scenario_prompt("test")
            
            assert prompt == "Test scenario"

    def test_get_scenario_prompt_nonexistent(self):
        """Test getting non-existent scenario prompt."""
        with tempfile.TemporaryDirectory() as temp_dir:
            loader = PromptLoader(Path(temp_dir))
            prompt = loader.get_scenario_prompt("nonexistent")
            
            assert prompt is None

    def test_get_all_system_prompts(self):
        """Test getting all system prompts."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            (temp_path / "prompt1.txt").write_text("Content 1")
            (temp_path / "prompt2.txt").write_text("Content 2")
            
            loader = PromptLoader(temp_path)
            prompts = loader.get_all_system_prompts()
            
            assert isinstance(prompts, dict)
            assert "prompt1" in prompts
            assert "prompt2" in prompts
            assert "system_base" in prompts  # Fallback

    def test_get_all_scenario_prompts(self):
        """Test getting all scenario prompts."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            scenarios_dir = temp_path / "scenarios"
            scenarios_dir.mkdir()
            (scenarios_dir / "system_scenario1.txt").write_text("Scenario 1")
            (scenarios_dir / "system_scenario2.txt").write_text("Scenario 2")
            
            loader = PromptLoader(temp_path)
            prompts = loader.get_all_scenario_prompts()
            
            assert isinstance(prompts, dict)
            assert "scenario1" in prompts
            assert "scenario2" in prompts

    def test_reload_prompts(self):
        """Test reloading prompts."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            (temp_path / "test.txt").write_text("Original content")
            
            loader = PromptLoader(temp_path)
            loader.load_all_prompts()
            
            # Modify file
            (temp_path / "test.txt").write_text("Modified content")
            
            # Reload
            loader.reload_prompts()
            
            prompt = loader.get_system_prompt("test")
            assert prompt == "Modified content"

    def test_get_base_system_prompt(self):
        """Test getting base system prompt."""
        loader = PromptLoader()
        prompt = loader._get_base_system_prompt()
        
        assert isinstance(prompt, str)
        assert "educational assistant" in prompt
        assert "children aged 7-11" in prompt
