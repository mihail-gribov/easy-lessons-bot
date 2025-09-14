"""Educational content formatting templates."""

import re
from typing import Dict


class EducationalTemplates:
    """Apply educational formatting patterns."""
    
    SUBJECT_EMOJIS = {
        'math': '📐',
        'science': '🔬', 
        'physics': '⚡',
        'chemistry': '⚗️',
        'biology': '🧬',
        'language': '📚',
        'history': '📜',
        'geography': '🌍',
        'general': '💡'
    }
    
    def apply_formatting(self, text: str, content_type: str) -> str:
        """Apply educational formatting patterns."""
        # Add subject emoji
        emoji = self.SUBJECT_EMOJIS.get(content_type, '💡')
        
        # Format common educational patterns
        text = self._format_examples(text)
        text = self._format_steps(text)
        text = self._format_results(text)
        text = self._format_definitions(text)
        
        return text
    
    def _format_examples(self, text: str) -> str:
        """Format example sections."""
        # Handle "Например:" and "Например," - use more specific patterns
        text = re.sub(r'^Например:', r'<b>📝 Например:</b>', text, flags=re.IGNORECASE)
        text = re.sub(r'^Например,', r'<b>📝 Например,</b>', text, flags=re.IGNORECASE)
        
        # Handle "Например:" in the middle of text (after newlines)
        text = re.sub(r'\nНапример:', r'\n<b>📝 Например:</b>', text, flags=re.IGNORECASE)
        text = re.sub(r'\nНапример,', r'\n<b>📝 Например,</b>', text, flags=re.IGNORECASE)
        
        # Handle "Например:" after double newlines
        text = re.sub(r'\n\nНапример:', r'\n\n<b>📝 Например:</b>', text, flags=re.IGNORECASE)
        text = re.sub(r'\n\nНапример,', r'\n\n<b>📝 Например,</b>', text, flags=re.IGNORECASE)
        
        # Handle "Пример:" only if it's not part of "Например:"
        # Use negative lookbehind to avoid matching "Пример:" inside "Например:"
        text = re.sub(r'(?<!На)Пример:', r'<b>📝 Пример:</b>', text, flags=re.IGNORECASE)
        
        return text
    
    def _format_steps(self, text: str) -> str:
        """Format step-by-step solutions."""
        # Handle at start of line
        text = re.sub(r'^Решение:', r'<b>🔍 Решение:</b>', text, flags=re.IGNORECASE)
        text = re.sub(r'^Шаги:', r'<b>📋 Шаги:</b>', text, flags=re.IGNORECASE)
        text = re.sub(r'^Алгоритм:', r'<b>⚙️ Алгоритм:</b>', text, flags=re.IGNORECASE)
        
        # Handle after newlines
        text = re.sub(r'\nРешение:', r'\n<b>🔍 Решение:</b>', text, flags=re.IGNORECASE)
        text = re.sub(r'\nШаги:', r'\n<b>📋 Шаги:</b>', text, flags=re.IGNORECASE)
        text = re.sub(r'\nАлгоритм:', r'\n<b>⚙️ Алгоритм:</b>', text, flags=re.IGNORECASE)
        
        # Format numbered lists
        text = re.sub(r'^(\d+)\.', r'• <b>\1.</b>', text, flags=re.MULTILINE)
        text = re.sub(r'^- ', r'• ', text, flags=re.MULTILINE)
        
        return text
    
    def _format_results(self, text: str) -> str:
        """Format answers and results."""
        # Handle at start of line
        text = re.sub(r'^Ответ:', r'<b>✅ Ответ:</b>', text, flags=re.IGNORECASE)
        text = re.sub(r'^Результат:', r'<b>✅ Результат:</b>', text, flags=re.IGNORECASE)
        text = re.sub(r'^Итог:', r'<b>✅ Итог:</b>', text, flags=re.IGNORECASE)
        
        # Handle after newlines
        text = re.sub(r'\nОтвет:', r'\n<b>✅ Ответ:</b>', text, flags=re.IGNORECASE)
        text = re.sub(r'\nРезультат:', r'\n<b>✅ Результат:</b>', text, flags=re.IGNORECASE)
        text = re.sub(r'\nИтог:', r'\n<b>✅ Итог:</b>', text, flags=re.IGNORECASE)
        
        # Handle after double newlines
        text = re.sub(r'\n\nОтвет:', r'\n\n<b>✅ Ответ:</b>', text, flags=re.IGNORECASE)
        text = re.sub(r'\n\nРезультат:', r'\n\n<b>✅ Результат:</b>', text, flags=re.IGNORECASE)
        text = re.sub(r'\n\nИтог:', r'\n\n<b>✅ Итог:</b>', text, flags=re.IGNORECASE)
        
        # Handle after periods and spaces
        text = re.sub(r'\. Ответ:', r'. <b>✅ Ответ:</b>', text, flags=re.IGNORECASE)
        text = re.sub(r'\. Результат:', r'. <b>✅ Результат:</b>', text, flags=re.IGNORECASE)
        text = re.sub(r'\. Итог:', r'. <b>✅ Итог:</b>', text, flags=re.IGNORECASE)
        
        return text
    
    def _format_definitions(self, text: str) -> str:
        """Format definitions and important terms."""
        # Handle at start of line
        text = re.sub(r'^Определение:', r'<b>📖 Определение:</b>', text, flags=re.IGNORECASE)
        text = re.sub(r'^Правило:', r'<b>📏 Правило:</b>', text, flags=re.IGNORECASE)
        text = re.sub(r'^Формула:', r'<b>🧮 Формула:</b>', text, flags=re.IGNORECASE)
        
        # Handle after newlines
        text = re.sub(r'\nОпределение:', r'\n<b>📖 Определение:</b>', text, flags=re.IGNORECASE)
        text = re.sub(r'\nПравило:', r'\n<b>📏 Правило:</b>', text, flags=re.IGNORECASE)
        text = re.sub(r'\nФормула:', r'\n<b>🧮 Формула:</b>', text, flags=re.IGNORECASE)
        
        return text
