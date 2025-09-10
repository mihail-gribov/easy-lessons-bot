"""LLM client for OpenRouter integration using OpenAI client."""

import asyncio
import logging
from typing import Any

from openai import AsyncOpenAI, RateLimitError, APITimeoutError, APIConnectionError, APIError

from settings.config import get_settings

logger = logging.getLogger(__name__)


class LLMError(Exception):
    """Base exception for LLM-related errors."""
    pass


class LLMTimeoutError(LLMError):
    """Raised when LLM request times out."""
    pass


class LLMRateLimitError(LLMError):
    """Raised when LLM rate limit is exceeded."""
    pass


class LLMConnectionError(LLMError):
    """Raised when LLM connection fails."""
    pass


class LLMAPIError(LLMError):
    """Raised when LLM API returns an error."""
    pass


class LLMClient:
    """Client for interacting with OpenRouter LLM API."""

    def __init__(self) -> None:
        """Initialize LLM client with settings."""
        self.settings = get_settings()
        self.client = AsyncOpenAI(
            api_key=self.settings.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
        )

    async def generate_response(
        self,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """
        Generate response from LLM.

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            temperature: LLM temperature (0.0-2.0)
            max_tokens: Maximum tokens in response

        Returns:
            Generated response text

        Raises:
            LLMTimeoutError: If request times out after retries
            LLMRateLimitError: If rate limit is exceeded
            LLMConnectionError: If connection fails
            LLMAPIError: If API returns an error
        """
        # Use settings defaults if not provided
        temperature = temperature or self.settings.llm_temperature
        max_tokens = max_tokens or self.settings.llm_max_tokens

        logger.info(
            "Sending LLM request: model=%s, temperature=%.2f, "
            "max_tokens=%d, messages=%d",
            self.settings.openrouter_model,
            temperature,
            max_tokens,
            len(messages),
        )

        # Retry logic: 1 retry for network/5xx errors
        for attempt in range(2):
            try:
                start_time = asyncio.get_event_loop().time()

                response = await asyncio.wait_for(
                    self.client.chat.completions.create(
                        model=self.settings.openrouter_model,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                    ),
                    timeout=30.0,  # 30 second timeout
                )

                duration_ms = int((asyncio.get_event_loop().time() - start_time) * 1000)

                # Extract response text
                response_text = response.choices[0].message.content or ""

                # Log successful response
                logger.info(
                    "LLM response received: duration=%dms, tokens=%d, length=%d",
                    duration_ms,
                    response.usage.total_tokens if response.usage else 0,
                    len(response_text),
                )

                return response_text

            except asyncio.TimeoutError:
                logger.warning("LLM request timeout (attempt %d/2)", attempt + 1)
                if attempt == 1:  # Last attempt
                    raise LLMTimeoutError("LLM request timeout after 2 attempts") from None

            except RateLimitError as e:
                logger.error("LLM rate limit exceeded: %s", e)
                raise LLMRateLimitError(f"Rate limit exceeded: {e}") from e

            except APIConnectionError as e:
                logger.warning("LLM connection error (attempt %d/2): %s", attempt + 1, e)
                if attempt == 0:
                    await asyncio.sleep(0.5)  # Wait 0.5s before retry
                    continue
                raise LLMConnectionError(f"Connection failed: {e}") from e

            except APITimeoutError as e:
                logger.warning("LLM API timeout (attempt %d/2): %s", attempt + 1, e)
                if attempt == 0:
                    await asyncio.sleep(0.5)  # Wait 0.5s before retry
                    continue
                raise LLMTimeoutError(f"API timeout: {e}") from e

            except APIError as e:
                # Check if it's a retryable 5xx error
                status_code = getattr(e, 'status_code', None)
                if status_code and 500 <= status_code < 600 and attempt == 0:
                    logger.warning("LLM 5xx error (attempt %d/2): %s", attempt + 1, e)
                    await asyncio.sleep(0.5)  # Wait 0.5s before retry
                    continue
                
                logger.error("LLM API error: %s", e)
                raise LLMAPIError(f"API error: {e}") from e

            except Exception as e:
                # Generic error handling for unexpected exceptions
                error_msg = str(e).lower()
                retryable_keywords = [
                    "network", "connection", "timeout", "5xx",
                    "500", "502", "503", "504",
                ]
                is_retryable = any(
                    keyword in error_msg for keyword in retryable_keywords
                )

                if is_retryable and attempt == 0:
                    logger.warning(
                        "Retryable LLM error (attempt %d/2): %s", attempt + 1, e,
                    )
                    await asyncio.sleep(0.5)  # Wait 0.5s before retry
                    continue

                logger.exception("Unexpected LLM error")
                raise LLMError(f"Unexpected error: {e}") from e

        # This should never be reached, but just in case
        raise LLMError("LLM request failed after all attempts")


# Global LLM client instance
_llm_client: LLMClient | None = None


def get_llm_client() -> LLMClient:
    """Get global LLM client instance."""
    global _llm_client  # noqa: PLW0603
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
