"""Main Telegram message formatter for educational content."""

import re
import time
import logging
from typing import Optional

from .math_converter import MathConverter
from .educational_templates import EducationalTemplates
from settings.config import get_settings

logger = logging.getLogger(__name__)


class TelegramFormatter:
    """Format educational content for optimal Telegram display."""
    
    def __init__(self):
        """Initialize the formatter."""
        self.settings = get_settings()
        self.math_converter = MathConverter()
        self.templates = EducationalTemplates()
    
    def format_message(self, text: str, content_type: str = "general") -> str:
        """
        Convert raw educational content to Telegram HTML format.
        
        Args:
            text: Raw text from LLM
            content_type: Type of content (math, science, language, general)
            
        Returns:
            HTML-formatted text ready for Telegram
        """
        # Check if formatting is enabled
        if not self.settings.enable_html_formatting:
            return text
        
        start_time = time.time()
        
        try:
            # Apply comprehensive formatting
            formatted_text = self._apply_basic_formatting(text, content_type)
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Check formatting time limit
            if duration_ms > self.settings.max_formatting_time_ms:
                logger.warning(
                    "Formatting took too long: %dms > %dms, using original text",
                    duration_ms, self.settings.max_formatting_time_ms
                )
                return text
            
            logger.info(
                "Formatted message: type=%s, input_length=%d, output_length=%d, duration_ms=%.2f",
                content_type, len(text), len(formatted_text), duration_ms
            )
            
            return formatted_text
            
        except Exception as e:
            logger.error("Formatting failed: %s, falling back to plain text", e)
            if self.settings.formatting_fallback_to_plain:
                return text  # Graceful degradation
            else:
                raise
    
    def _apply_basic_formatting(self, text: str, content_type: str = "general") -> str:
        """Apply basic formatting to text."""
        # Use default content type if not specified
        if not content_type or content_type == "general":
            content_type = self.settings.default_content_type
        
        # Convert LaTeX-like expressions (if enabled)
        if self.settings.use_mathematical_unicode:
            text = self.math_converter.convert_math_expressions(text)
        
        # Apply educational formatting (if enabled)
        if self.settings.use_educational_emojis:
            text = self.templates.apply_formatting(text, content_type)
        
        # Basic markdown to HTML conversion (after educational formatting)
        text = self._convert_markdown_to_html(text)
        
        return text
    
    def _convert_markdown_to_html(self, text: str) -> str:
        """Convert basic markdown syntax to HTML."""
        # Bold: **text** -> <b>text</b>
        text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
        
        # Italic: *text* -> <i>text</i>
        text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
        
        # Code: `text` -> <code>text</code>
        text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
        
        # Headers: lines that look like headers (standalone lines with specific patterns)
        # This handles cases where extracted text contains unformatted headers
        text = self._format_headers(text)
        
        return text
    
    def _format_headers(self, text: str) -> str:
        """Format headers in extracted text for better Telegram display."""
        lines = text.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                formatted_lines.append('')
                continue
            
            # Check if line looks like a header
            # Headers are typically short, standalone lines that don't end with punctuation
            # and contain specific keywords or patterns
            if self._is_header_line(line):
                formatted_lines.append(f'<b>{line}</b>')
            else:
                # Check if line contains a header within it (e.g., "Я вижу текст: Заголовок")
                formatted_line = self._extract_and_format_embedded_headers(line)
                formatted_lines.append(formatted_line)
        
        return '\n'.join(formatted_lines)
    
    def _extract_and_format_embedded_headers(self, line: str) -> str:
        """Extract and format headers that are embedded within a line."""
        # Very conservative approach: only format if the part after colon looks like a clear header
        # Pattern: "Text: Header" where Header is short and doesn't contain verbs
        match = re.match(r'^(.*?):\s*(.+)$', line)
        if match:
            prefix = match.group(1)
            potential_header = match.group(2).strip()
            
            # Check if the potential header looks like a real header
            if self._is_header_line(potential_header):
                return f"{prefix}: <b>{potential_header}</b>"
        
        return line
    
    def _is_header_line(self, line: str) -> bool:
        """Check if a line looks like a header."""
        # Skip empty lines
        if not line or len(line.strip()) == 0:
            return False
        
        # Skip lines that are too long (likely not headers)
        if len(line) > 100:
            return False
        
        # Skip lines that end with punctuation (likely not headers)
        if line.endswith(('.', '!', '?', ':', ';', ',')):
            return False
        
        # Skip lines that start with numbers or bullets
        if re.match(r'^\d+\.', line) or re.match(r'^[-*•]', line):
            return False
        
        # Skip lines that start with common sentence starters
        sentence_starters = ['я вижу', 'я вижу:', 'я вижу текст:', 'я вижу математическую', 'я вижу физическую', 'я вижу химическую', 'я вижу историческую', 'я вижу географическую', 'я вижу литературную', 'я вижу языковую']
        if any(line.lower().startswith(starter) for starter in sentence_starters):
            return False
        
        # Very conservative approach: only format lines that are clearly standalone headers
        # Check if line is a short, standalone phrase without verbs
        words = line.split()
        if len(words) <= 6 and len(words) >= 2:
            # Headers typically don't contain verbs in past tense or present tense
            verb_indicators = ['был', 'была', 'было', 'были', 'есть', 'является', 'являются', 'находится', 'находятся', 'вижу', 'вижу:', 'вижу текст:', 'поставили', 'перевезли', 'взимали', 'брали']
            if not any(verb in line.lower() for verb in verb_indicators):
                # Additional check: should not contain common sentence words
                sentence_words = ['в', 'на', 'с', 'по', 'для', 'от', 'до', 'из', 'к', 'у', 'о', 'об', 'при', 'через', 'между', 'среди', 'вокруг', 'около', 'возле', 'близ', 'далеко', 'рядом']
                # If the line contains too many prepositions, it's likely not a header
                preposition_count = sum(1 for word in words if word.lower() in sentence_words)
                if preposition_count <= 2:  # Allow up to 2 prepositions for compound headers
                    return True
        
        return False
