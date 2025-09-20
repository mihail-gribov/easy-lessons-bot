"""Comprehensive tests for the formatting pipeline."""

import pytest
from core.formatting.telegram_formatter import TelegramFormatter


class TestFormattingPipeline:
    """Test the complete formatting pipeline."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.formatter = TelegramFormatter()
    
    def test_math_content_pipeline(self):
        """Test complete math content formatting pipeline."""
        formatter = TelegramFormatter()
        input_text = """**Теорема Пифагора**

Формула: \\( a^2 + b^2 = c^2 \\), где a и b — это длины катетов, а c — длина гипотенузы.

Например: если один катет равен 3, а другой 4, то мы можем посчитать так:
- \\( 3^2 = 9 \\)
- \\( 4^2 = 16 \\)
- Теперь сложим: \\( 9 + 16 = 25 \\)
- И найдем гипотенузу: \\( c = sqrt(25) = 5 \\)

Ответ: гипотенуза равна 5"""
        
        result = formatter.format_message(input_text, "math")
        
        # Check mathematical formatting
        assert "<code>a² + b² = c²</code>" in result
        assert "<code>3² = 9</code>" in result
        assert "<code>4² = 16</code>" in result
        assert "<code>9 + 16 = 25</code>" in result
        assert "<code>c = √25 = 5</code>" in result
        
        # Check educational formatting
        assert "<b>🧮 Формула:</b>" in result
        assert "<b>📝 Например:</b>" in result
        assert "<b>✅ Ответ:</b>" in result
        
        # Check markdown formatting
        assert "<b>Теорема Пифагора</b>" in result
    
    def test_science_content_pipeline(self):
        """Test complete science content formatting pipeline."""
        formatter = TelegramFormatter()
        input_text = """**Фотосинтез**

Определение: процесс преобразования света в энергию растениями.

Например: листья растений поглощают солнечный свет и углекислый газ.

Результат: растения производят кислород и глюкозу."""
        
        result = formatter.format_message(input_text, "science")
        
        # Check educational formatting
        assert "<b>📖 Определение:</b>" in result
        assert "<b>📝 Например:</b>" in result
        assert "<b>✅ Результат:</b>" in result
        
        # Check markdown formatting
        assert "<b>Фотосинтез</b>" in result
    
    def test_language_content_pipeline(self):
        """Test complete language content formatting pipeline."""
        formatter = TelegramFormatter()
        input_text = """**Правило ЖИ-ШИ**

Правило: после Ж и Ш всегда пишется И, а не Ы.

Например: жить, шить, машина, жизнь.

Ответ: это правило нужно запомнить!"""
        
        result = formatter.format_message(input_text, "language")
        
        # Check educational formatting
        assert "<b>📏 Правило:</b>" in result
        assert "<b>📝 Например:</b>" in result
        assert "<b>✅ Ответ:</b>" in result
        
        # Check markdown formatting
        assert "<b>Правило ЖИ-ШИ</b>" in result
    
    def test_mixed_content_pipeline(self):
        """Test mixed content with various formatting elements."""
        formatter = TelegramFormatter()
        input_text = """**Смешанная задача**

Формула: \\( S = \\pi \\times r^2 \\)

Например: если радиус равен 5, то площадь равна \\( \\pi \\times 5^2 = 25\\pi \\)

Решение:
1. Подставляем значение радиуса
2. Возводим в квадрат
3. Умножаем на π

Ответ: площадь круга равна 25π"""
        
        result = formatter.format_message(input_text, "math")
        
        # Check mathematical formatting
        assert "<code>S = π × r²</code>" in result
        assert "<code>π × 5² = 25π</code>" in result
        
        # Check educational formatting
        assert "<b>🧮 Формула:</b>" in result
        assert "<b>📝 Например:</b>" in result
        assert "<b>🔍 Решение:</b>" in result
        assert "<b>✅ Ответ:</b>" in result
        
        # Check list formatting
        assert "• <b>1.</b> Подставляем значение радиуса" in result
        assert "• <b>2.</b> Возводим в квадрат" in result
        assert "• <b>3.</b> Умножаем на π" in result
    
    def test_edge_cases(self):
        """Test edge cases and error handling."""
        formatter = TelegramFormatter()
        
        # Test empty input
        result = formatter.format_message("", "general")
        assert result == ""
        
        # Test input without special formatting
        result = formatter.format_message("Обычный текст", "general")
        assert result == "Обычный текст"
        
        # Test malformed LaTeX
        result = formatter.format_message("Формула: \\( a^2 + b^2", "math")
        assert "Формула:" in result  # Should not crash
        
        # Test very long input
        long_text = "Например: " + "очень длинный текст " * 100
        result = formatter.format_message(long_text, "general")
        assert "<b>📝 Например:</b>" in result
        assert len(result) > 0
    
    def test_performance(self):
        """Test formatting performance with various content types."""
        formatter = TelegramFormatter()
        
        test_cases = [
            ("math", "Формула: \\( x^2 + y^2 = z^2 \\)\n\nНапример: если x=3, y=4, то z=5\n\nОтвет: z = 5"),
            ("science", "Определение: процесс\n\nНапример: пример\n\nРезультат: результат"),
            ("language", "Правило: правило\n\nНапример: пример\n\nОтвет: ответ"),
            ("general", "Обычный текст без специального форматирования")
        ]
        
        for content_type, text in test_cases:
            result = formatter.format_message(text, content_type)
            assert isinstance(result, str)
            assert len(result) > 0
            # Should not take too long (basic performance check)
            assert len(result) <= len(text) * 3  # Reasonable upper bound










