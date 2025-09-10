"""User-friendly error messages for different error types."""

import random

from core.llm_client import (
    LLMAPIError,
    LLMConnectionError,
    LLMError,
    LLMRateLimitError,
    LLMTimeoutError,
)


class ErrorMessageStore:
    """Manages user-friendly error messages for different error types."""

    def __init__(self) -> None:
        """Initialize error message store."""
        self._messages: dict[type, list[str]] = {
            LLMTimeoutError: [
                "⏰ Упс! Я думаю слишком долго. Попробуй задать вопрос еще раз!",
                "🕐 Кажется, я задумался. Давай попробуем еще раз!",
                "⏱️ Время истекло! Попробуй переформулировать вопрос.",
            ],
            LLMRateLimitError: [
                "🚦 Слишком много вопросов! Подожди немного и попробуй снова.",
                "⏳ Я получил слишком много запросов. Давай подождем минуту!",
                "🔄 Сейчас у меня много работы. Попробуй через минуту!",
            ],
            LLMConnectionError: [
                "🌐 Проблемы с интернетом! Проверь соединение и попробуй снова.",
                "📡 Не могу подключиться к серверу. Попробуй позже!",
                "🔌 Проблемы с сетью. Давай попробуем еще раз!",
            ],
            LLMAPIError: [
                "🤖 У меня технические проблемы. Попробуй еще раз!",
                "⚙️ Что-то пошло не так с моими системами. Попробуй позже!",
                "🔧 Техническая неполадка. Давай попробуем еще раз!",
            ],
            LLMError: [
                "😔 Извини, у меня возникла проблема. Попробуй еще раз!",
                "🤷‍♂️ Что-то пошло не так. Попробуй переформулировать вопрос!",
                "😅 Упс! Попробуй задать вопрос по-другому!",
            ],
        }

        # Generic fallback messages
        self._generic_messages = [
            "😔 Извини, у меня возникла проблема с обработкой твоего сообщения. "
            "Попробуй еще раз или напиши что-то другое!",
            "🤷‍♂️ Что-то пошло не так. Попробуй переформулировать вопрос!",
            "😅 Упс! Попробуй задать вопрос по-другому!",
        ]

    def get_error_message(self, error: Exception) -> str:
        """
        Get user-friendly error message for given exception.

        Args:
            error: Exception that occurred

        Returns:
            User-friendly error message
        """
        # Try to find specific message for the error type
        for error_type, messages in self._messages.items():
            if isinstance(error, error_type):
                return random.choice(messages)

        # Check if it's a generic LLM error
        if isinstance(error, LLMError):
            return random.choice(self._messages[LLMError])

        # Fallback to generic message
        return random.choice(self._generic_messages)

    def get_generic_error_message(self) -> str:
        """
        Get a generic error message when error type is unknown.

        Returns:
            Generic user-friendly error message
        """
        return random.choice(self._generic_messages)


# Global error message store instance
_error_message_store: ErrorMessageStore | None = None


def get_error_message_store() -> ErrorMessageStore:
    """Get global error message store instance."""
    global _error_message_store  # noqa: PLW0603
    if _error_message_store is None:
        _error_message_store = ErrorMessageStore()
    return _error_message_store


def get_user_friendly_error_message(error: Exception) -> str:
    """
    Get user-friendly error message for given exception.

    Args:
        error: Exception that occurred

    Returns:
        User-friendly error message
    """
    store = get_error_message_store()
    return store.get_error_message(error)
