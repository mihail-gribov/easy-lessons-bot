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
        
        return text
