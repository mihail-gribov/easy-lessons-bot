"""Convert mathematical expressions for Telegram display."""

import re
from typing import Dict


class MathConverter:
    """Handle mathematical expression conversion."""
    
    # Unicode mathematical symbols
    MATH_SYMBOLS = {
        'sqrt': '√',
        'infinity': '∞',
        'sum': '∑',
        'product': '∏',
        'integral': '∫',
        'partial': '∂',
        'delta': 'Δ',
        'pi': 'π',
        'alpha': 'α',
        'beta': 'β',
        'gamma': 'γ',
        'theta': 'θ',
        'lambda': 'λ',
        'mu': 'μ',
        'sigma': 'σ',
        'phi': 'φ',
        'plus_minus': '±',
        'times': '×',
        'divide': '÷',
        'not_equal': '≠',
        'less_equal': '≤',
        'greater_equal': '≥',
        'approximately': '≈',
    }
    
    # Superscript digits for powers
    SUPERSCRIPTS = str.maketrans('0123456789', '⁰¹²³⁴⁵⁶⁷⁸⁹')
    
    def convert_math_expressions(self, text: str) -> str:
        """Convert LaTeX-like math to Unicode and HTML."""
        # First, convert powers: x^2 -> x² (before LaTeX processing)
        text = re.sub(r'(\w+)\^(\d+)', self._convert_power, text)
        
        # Convert square roots: sqrt(x) -> √x
        text = re.sub(r'sqrt\(([^)]+)\)', r'√\1', text)
        
        # Convert common mathematical symbols
        for symbol, unicode_char in self.MATH_SYMBOLS.items():
            text = text.replace(f'\\{symbol}', unicode_char)
        
        # Convert \( ... \) to <code>...</code> (after other conversions)
        text = re.sub(r'\\\(([^)]+)\\\)', lambda m: f'<code>{m.group(1).strip()}</code>', text)
        
        return text
    
    def _convert_power(self, match) -> str:
        """Convert power notation to superscript."""
        base = match.group(1)
        power = match.group(2)
        superscript_power = power.translate(self.SUPERSCRIPTS)
        return f"{base}{superscript_power}"
