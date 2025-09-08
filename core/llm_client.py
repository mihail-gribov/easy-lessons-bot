"""LLM client for OpenRouter integration using OpenAI client."""

import asyncio
import logging

from openai import AsyncOpenAI

from settings.config import get_settings

logger = logging.getLogger(__name__)


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
            Exception: If LLM request fails after retries
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

            except TimeoutError:
                logger.warning("LLM request timeout (attempt %d/2)", attempt + 1)
                if attempt == 1:  # Last attempt
                    timeout_msg = "LLM request timeout after 2 attempts"
                    raise Exception(timeout_msg) from None

            except Exception as e:
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

                logger.exception("LLM request failed")
                failed_msg = f"LLM request failed: {e}"
                raise Exception(failed_msg) from e

        # This should never be reached, but just in case
        final_msg = "LLM request failed after all attempts"
        raise Exception(final_msg)


# Global LLM client instance
_llm_client: LLMClient | None = None


def get_llm_client() -> LLMClient:
    """Get global LLM client instance."""
    global _llm_client  # noqa: PLW0603
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
