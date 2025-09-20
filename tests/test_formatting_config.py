"""Tests for formatting configuration."""

import pytest
from unittest.mock import patch
from core.formatting.telegram_formatter import TelegramFormatter


class TestFormattingConfiguration:
    """Test formatting configuration and settings."""
    
    def test_formatting_disabled(self):
        """Test formatting when disabled in settings."""
        with patch('core.formatting.telegram_formatter.get_settings') as mock_settings:
            mock_settings.return_value.enable_html_formatting = False
            mock_settings.return_value.formatting_fallback_to_plain = True
            mock_settings.return_value.max_formatting_time_ms = 100
            mock_settings.return_value.use_mathematical_unicode = True
            mock_settings.return_value.use_educational_emojis = True
            mock_settings.return_value.default_content_type = "general"
            
            formatter = TelegramFormatter()
            input_text = "**Bold text** и Например: пример"
            result = formatter.format_message(input_text, "math")
            
            # Should return original text when formatting is disabled
            assert result == input_text
    
    def test_mathematical_unicode_disabled(self):
        """Test formatting when mathematical Unicode is disabled."""
        with patch('core.formatting.telegram_formatter.get_settings') as mock_settings:
            mock_settings.return_value.enable_html_formatting = True
            mock_settings.return_value.formatting_fallback_to_plain = True
            mock_settings.return_value.max_formatting_time_ms = 100
            mock_settings.return_value.use_mathematical_unicode = False
            mock_settings.return_value.use_educational_emojis = True
            mock_settings.return_value.default_content_type = "general"
            
            formatter = TelegramFormatter()
            input_text = "x^2 + y^2 = z^2"
            result = formatter.format_message(input_text, "math")
            
            # Should not convert mathematical expressions
            assert "x^2" in result
            assert "x²" not in result
    
    def test_educational_emojis_disabled(self):
        """Test formatting when educational emojis are disabled."""
        with patch('core.formatting.telegram_formatter.get_settings') as mock_settings:
            mock_settings.return_value.enable_html_formatting = True
            mock_settings.return_value.formatting_fallback_to_plain = True
            mock_settings.return_value.max_formatting_time_ms = 100
            mock_settings.return_value.use_mathematical_unicode = True
            mock_settings.return_value.use_educational_emojis = False
            mock_settings.return_value.default_content_type = "general"
            
            formatter = TelegramFormatter()
            input_text = "Например: пример"
            result = formatter.format_message(input_text, "math")
            
            # Should not add educational emojis
            assert "📝" not in result
            assert "Например:" in result
    
    def test_default_content_type(self):
        """Test default content type setting."""
        with patch('core.formatting.telegram_formatter.get_settings') as mock_settings:
            mock_settings.return_value.enable_html_formatting = True
            mock_settings.return_value.formatting_fallback_to_plain = True
            mock_settings.return_value.max_formatting_time_ms = 100
            mock_settings.return_value.use_mathematical_unicode = True
            mock_settings.return_value.use_educational_emojis = True
            mock_settings.return_value.default_content_type = "science"
            
            formatter = TelegramFormatter()
            input_text = "Например: пример"
            result = formatter.format_message(input_text, "general")
            
            # Should use default content type
            assert "<b>📝 Например:</b>" in result
    
    def test_formatting_time_limit(self):
        """Test formatting time limit."""
        with patch('core.formatting.telegram_formatter.get_settings') as mock_settings:
            mock_settings.return_value.enable_html_formatting = True
            mock_settings.return_value.formatting_fallback_to_plain = True
            mock_settings.return_value.max_formatting_time_ms = 1  # Very short limit
            mock_settings.return_value.use_mathematical_unicode = True
            mock_settings.return_value.use_educational_emojis = True
            mock_settings.return_value.default_content_type = "general"
            
            formatter = TelegramFormatter()
            input_text = "**Bold text**"
            
            # Mock time to simulate slow formatting
            with patch('time.time') as mock_time:
                mock_time.side_effect = [0, 0.002]  # 2ms > 1ms limit
                result = formatter.format_message(input_text, "math")
                
                # Should return original text when time limit exceeded
                assert result == input_text
    
    def test_fallback_disabled(self):
        """Test behavior when fallback is disabled."""
        with patch('core.formatting.telegram_formatter.get_settings') as mock_settings:
            mock_settings.return_value.enable_html_formatting = True
            mock_settings.return_value.formatting_fallback_to_plain = False
            mock_settings.return_value.max_formatting_time_ms = 100
            mock_settings.return_value.use_mathematical_unicode = True
            mock_settings.return_value.use_educational_emojis = True
            mock_settings.return_value.default_content_type = "general"
            
            formatter = TelegramFormatter()
            input_text = "**Bold text**"
            
            # Mock an exception in formatting
            with patch.object(formatter, '_apply_basic_formatting', side_effect=Exception("Test error")):
                with pytest.raises(Exception, match="Test error"):
                    formatter.format_message(input_text, "math")
    
    def test_all_features_enabled(self):
        """Test formatting with all features enabled."""
        with patch('core.formatting.telegram_formatter.get_settings') as mock_settings:
            mock_settings.return_value.enable_html_formatting = True
            mock_settings.return_value.formatting_fallback_to_plain = True
            mock_settings.return_value.max_formatting_time_ms = 100
            mock_settings.return_value.use_mathematical_unicode = True
            mock_settings.return_value.use_educational_emojis = True
            mock_settings.return_value.default_content_type = "math"
            
            formatter = TelegramFormatter()
            input_text = "**Формула:** \\( x^2 + y^2 = z^2 \\)\n\nНапример: если x=3, y=4, то z=5\n\nОтвет: z = 5"
            result = formatter.format_message(input_text, "math")
            
            # Should apply all formatting
            assert "<b>Формула:</b>" in result
            assert "<code>x² + y² = z²</code>" in result
            assert "<b>📝 Например:</b>" in result
            assert "<b>✅ Ответ:</b>" in result










