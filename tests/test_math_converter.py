"""Tests for MathConverter."""

import pytest
from core.formatting.math_converter import MathConverter


class TestMathConverter:
    """Test mathematical expression conversion."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.converter = MathConverter()
    
    def test_latex_conversion(self):
        """Test LaTeX expression conversion."""
        converter = MathConverter()
        input_text = r"Формула: \( a^2 + b^2 = c^2 \)"
        result = converter.convert_math_expressions(input_text)
        assert "<code>a² + b² = c²</code>" in result
    
    def test_power_conversion(self):
        """Test power notation conversion."""
        converter = MathConverter()
        input_text = "x^2 + y^3 = z^10"
        result = converter.convert_math_expressions(input_text)
        assert "x² + y³ = z¹⁰" in result
    
    def test_square_root_conversion(self):
        """Test square root conversion."""
        converter = MathConverter()
        input_text = "sqrt(25) = 5"
        result = converter.convert_math_expressions(input_text)
        assert "√25 = 5" in result
    
    def test_math_symbols_conversion(self):
        """Test mathematical symbols conversion."""
        converter = MathConverter()
        input_text = r"\pi \alpha \beta \gamma"
        result = converter.convert_math_expressions(input_text)
        assert "π α β γ" in result
    
    def test_complex_expression(self):
        """Test complex mathematical expression."""
        converter = MathConverter()
        input_text = r"Формула: \( x^2 + sqrt(y) = z^3 \)"
        result = converter.convert_math_expressions(input_text)
        assert "<code>x² + √y = z³</code>" in result
    
    def test_no_math_expressions(self):
        """Test text without mathematical expressions."""
        converter = MathConverter()
        input_text = "Обычный текст без математики"
        result = converter.convert_math_expressions(input_text)
        assert result == input_text
    
    def test_empty_input(self):
        """Test empty input."""
        converter = MathConverter()
        result = converter.convert_math_expressions("")
        assert result == ""
