"""Basic tests for TelegramFormatter."""

import pytest
from core.formatting.telegram_formatter import TelegramFormatter


class TestTelegramFormatterBasic:
    """Test basic functionality of TelegramFormatter."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.formatter = TelegramFormatter()
    
    def test_basic_formatting(self):
        """Test basic text formatting."""
        formatter = TelegramFormatter()
        input_text = "Обычный текст"
        result = formatter.format_message(input_text, "general")
        assert result == input_text
    
    def test_markdown_bold_conversion(self):
        """Test bold markdown conversion."""
        formatter = TelegramFormatter()
        input_text = "**Важный текст**"
        result = formatter.format_message(input_text, "general")
        assert "<b>Важный текст</b>" in result
    
    def test_markdown_italic_conversion(self):
        """Test italic markdown conversion."""
        formatter = TelegramFormatter()
        input_text = "*Курсивный текст*"
        result = formatter.format_message(input_text, "general")
        assert "<i>Курсивный текст</i>" in result
    
    def test_markdown_code_conversion(self):
        """Test code markdown conversion."""
        formatter = TelegramFormatter()
        input_text = "`код`"
        result = formatter.format_message(input_text, "general")
        assert "<code>код</code>" in result
    
    def test_graceful_degradation(self):
        """Test handling of malformed input."""
        formatter = TelegramFormatter()
        input_text = "Обычный текст без специального форматирования"
        result = formatter.format_message(input_text, "general")
        # Should not raise exceptions and return some reasonable output
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_empty_input(self):
        """Test handling of empty input."""
        formatter = TelegramFormatter()
        result = formatter.format_message("", "general")
        assert result == ""
    
    def test_latex_conversion(self):
        """Test LaTeX expression conversion."""
        formatter = TelegramFormatter()
        input_text = r"Формула: \( a^2 + b^2 = c^2 \)"
        result = formatter.format_message(input_text, "math")
        assert "<code>a² + b² = c²</code>" in result
    
    def test_power_conversion(self):
        """Test power notation conversion."""
        formatter = TelegramFormatter()
        input_text = "x^2 + y^3 = z^10"
        result = formatter.format_message(input_text, "math")
        assert "x² + y³ = z¹⁰" in result
    
    def test_combined_formatting(self):
        """Test combined markdown and math formatting."""
        formatter = TelegramFormatter()
        input_text = r"**Формула:** \( x^2 + y^2 = z^2 \)"
        result = formatter.format_message(input_text, "math")
        assert "<b>Формула:</b>" in result
        assert "<code>x² + y² = z²</code>" in result
    
    def test_educational_formatting(self):
        """Test educational pattern formatting."""
        formatter = TelegramFormatter()
        input_text = "Например: решение задачи. Ответ: 42"
        result = formatter.format_message(input_text, "math")
        assert "<b>📝 Например:</b>" in result
        assert "<b>✅ Ответ:</b>" in result
    
    def test_comprehensive_formatting(self):
        """Test comprehensive formatting with all features."""
        formatter = TelegramFormatter()
        input_text = "**Формула:** \\( x^2 + y^2 = z^2 \\)\n\nНапример: если x=3, y=4, то z=5\n\nОтвет: z = 5"
        result = formatter.format_message(input_text, "math")
        assert "<b>Формула:</b>" in result
        assert "<code>x² + y² = z²</code>" in result
        assert "<b>📝 Например:</b>" in result
        assert "<b>✅ Ответ:</b>" in result
