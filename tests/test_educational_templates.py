"""Tests for EducationalTemplates."""

import pytest
from core.formatting.educational_templates import EducationalTemplates


class TestEducationalTemplates:
    """Test educational formatting patterns."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.templates = EducationalTemplates()
    
    def test_example_formatting(self):
        """Test example section formatting."""
        templates = EducationalTemplates()
        input_text = "Например: это пример"
        result = templates.apply_formatting(input_text, "math")
        assert "<b>📝 Например:</b>" in result
    
    def test_solution_formatting(self):
        """Test solution section formatting."""
        templates = EducationalTemplates()
        input_text = "Решение: пошаговое решение"
        result = templates.apply_formatting(input_text, "math")
        assert "<b>🔍 Решение:</b>" in result
    
    def test_answer_formatting(self):
        """Test answer section formatting."""
        templates = EducationalTemplates()
        input_text = "Ответ: 42"
        result = templates.apply_formatting(input_text, "math")
        assert "<b>✅ Ответ:</b>" in result
    
    def test_definition_formatting(self):
        """Test definition section formatting."""
        templates = EducationalTemplates()
        input_text = "Определение: важное понятие"
        result = templates.apply_formatting(input_text, "general")
        assert "<b>📖 Определение:</b>" in result
    
    def test_formula_formatting(self):
        """Test formula section formatting."""
        templates = EducationalTemplates()
        input_text = "Формула: a^2 + b^2 = c^2"
        result = templates.apply_formatting(input_text, "math")
        assert "<b>🧮 Формула:</b>" in result
    
    def test_numbered_list_formatting(self):
        """Test numbered list formatting."""
        templates = EducationalTemplates()
        input_text = "1. Первый шаг\n2. Второй шаг"
        result = templates.apply_formatting(input_text, "math")
        assert "• <b>1.</b> Первый шаг" in result
        assert "• <b>2.</b> Второй шаг" in result
    
    def test_bullet_list_formatting(self):
        """Test bullet list formatting."""
        templates = EducationalTemplates()
        input_text = "- Первый пункт\n- Второй пункт"
        result = templates.apply_formatting(input_text, "math")
        assert "• Первый пункт" in result
        assert "• Второй пункт" in result
    
    def test_case_insensitive_formatting(self):
        """Test case insensitive formatting."""
        templates = EducationalTemplates()
        input_text = "например: пример в нижнем регистре"
        result = templates.apply_formatting(input_text, "math")
        assert "<b>📝 Например:</b>" in result
    
    def test_no_formatting_needed(self):
        """Test text that doesn't need formatting."""
        templates = EducationalTemplates()
        input_text = "Обычный текст без специальных паттернов"
        result = templates.apply_formatting(input_text, "general")
        assert result == input_text
    
    def test_empty_input(self):
        """Test empty input."""
        templates = EducationalTemplates()
        result = templates.apply_formatting("", "general")
        assert result == ""








