"""Tests for LLM client functionality."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from openai import APIConnectionError, APIError, APITimeoutError, RateLimitError

from core.llm_client import (
    LLMAPIError,
    LLMClient,
    LLMConnectionError,
    LLMError,
    LLMRateLimitError,
    LLMTimeoutError,
    get_llm_client,
)


class TestLLMClient:
    """Test cases for LLMClient class."""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing."""
        with patch("core.llm_client.get_settings") as mock:
            mock_settings = MagicMock()
            mock_settings.openrouter_api_key = "test_api_key"
            mock_settings.openrouter_model = "gpt-4o-mini"
            mock_settings.llm_temperature = 0.9
            mock_settings.llm_max_tokens = 1000
            mock.return_value = mock_settings
            yield mock_settings

    @pytest.fixture
    def llm_client(self, mock_settings):
        """Create LLM client for testing."""
        return LLMClient()

    def test_llm_client_initialization(self, llm_client, mock_settings):
        """Test LLM client initialization."""
        assert llm_client.settings == mock_settings
        assert llm_client.client is not None

    @pytest.mark.asyncio
    async def test_generate_response_success(self, llm_client):
        """Test successful response generation."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test response"
        mock_response.usage = MagicMock()
        mock_response.usage.total_tokens = 150

        llm_client.client.chat.completions.create = AsyncMock(
            return_value=mock_response
        )

        messages = [{"role": "user", "content": "Hello"}]
        response = await llm_client.generate_response(messages)

        assert response == "Test response"
        llm_client.client.chat.completions.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_response_with_custom_params(self, llm_client):
        """Test response generation with custom parameters."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Custom response"
        mock_response.usage = None

        llm_client.client.chat.completions.create = AsyncMock(
            return_value=mock_response
        )

        messages = [{"role": "user", "content": "Test"}]
        response = await llm_client.generate_response(
            messages,
            temperature=0.5,
            max_tokens=500,
        )

        assert response == "Custom response"

        # Check that custom parameters were used
        call_args = llm_client.client.chat.completions.create.call_args
        assert call_args[1]["temperature"] == 0.5
        assert call_args[1]["max_tokens"] == 500

    @pytest.mark.asyncio
    async def test_generate_response_uses_default_params(
        self, llm_client, mock_settings
    ):
        """Test that default parameters from settings are used."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Default response"
        mock_response.usage = None

        llm_client.client.chat.completions.create = AsyncMock(
            return_value=mock_response
        )

        messages = [{"role": "user", "content": "Test"}]
        await llm_client.generate_response(messages)

        # Check that default parameters were used
        call_args = llm_client.client.chat.completions.create.call_args
        assert call_args[1]["temperature"] == mock_settings.llm_temperature
        assert call_args[1]["max_tokens"] == mock_settings.llm_max_tokens
        assert call_args[1]["model"] == mock_settings.openrouter_model

    @pytest.mark.asyncio
    async def test_generate_response_timeout_error(self, llm_client):
        """Test timeout error handling."""
        llm_client.client.chat.completions.create = AsyncMock(
            side_effect=TimeoutError("Request timeout"),
        )

        messages = [{"role": "user", "content": "Test"}]

        with pytest.raises(LLMTimeoutError):
            await llm_client.generate_response(messages)

    @pytest.mark.asyncio
    async def test_generate_response_rate_limit_error(self, llm_client):
        """Test rate limit error handling."""
        # Create a proper RateLimitError
        mock_response = MagicMock()
        mock_response.request = MagicMock()
        error = RateLimitError("Rate limit exceeded", response=mock_response, body=None)

        llm_client.client.chat.completions.create = AsyncMock(side_effect=error)

        messages = [{"role": "user", "content": "Test"}]

        with pytest.raises(LLMRateLimitError):
            await llm_client.generate_response(messages)

    @pytest.mark.asyncio
    async def test_generate_response_connection_error_retry_success(self, llm_client):
        """Test connection error with successful retry."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Retry success"
        mock_response.usage = None

        # Create proper APIConnectionError
        mock_request = MagicMock()
        error = APIConnectionError(request=mock_request, message="Connection failed")

        llm_client.client.chat.completions.create = AsyncMock(
            side_effect=[error, mock_response],
        )

        messages = [{"role": "user", "content": "Test"}]
        response = await llm_client.generate_response(messages)

        assert response == "Retry success"
        assert llm_client.client.chat.completions.create.call_count == 2

    @pytest.mark.asyncio
    async def test_generate_response_connection_error_retry_failure(self, llm_client):
        """Test connection error with failed retry."""
        # Create proper APIConnectionError
        mock_request = MagicMock()
        error = APIConnectionError(request=mock_request, message="Connection failed")

        llm_client.client.chat.completions.create = AsyncMock(side_effect=error)

        messages = [{"role": "user", "content": "Test"}]

        with pytest.raises(LLMConnectionError):
            await llm_client.generate_response(messages)

    @pytest.mark.asyncio
    async def test_generate_response_api_timeout_retry_success(self, llm_client):
        """Test API timeout with successful retry."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Timeout retry success"
        mock_response.usage = None

        llm_client.client.chat.completions.create = AsyncMock(
            side_effect=[
                APITimeoutError("API timeout"),
                mock_response,
            ],
        )

        messages = [{"role": "user", "content": "Test"}]
        response = await llm_client.generate_response(messages)

        assert response == "Timeout retry success"
        assert llm_client.client.chat.completions.create.call_count == 2

    @pytest.mark.asyncio
    async def test_generate_response_api_timeout_retry_failure(self, llm_client):
        """Test API timeout with failed retry."""
        # Create proper APITimeoutError
        mock_request = MagicMock()
        error = APITimeoutError(request=mock_request)

        llm_client.client.chat.completions.create = AsyncMock(side_effect=error)

        messages = [{"role": "user", "content": "Test"}]

        with pytest.raises(LLMConnectionError):
            await llm_client.generate_response(messages)

    @pytest.mark.asyncio
    async def test_generate_response_5xx_error_retry_success(self, llm_client):
        """Test 5xx error with successful retry."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "5xx retry success"
        mock_response.usage = None

        # Create 5xx error
        mock_request = MagicMock()
        error = APIError(
            message="Internal server error", request=mock_request, body=None
        )
        error.status_code = 500

        llm_client.client.chat.completions.create = AsyncMock(
            side_effect=[error, mock_response],
        )

        messages = [{"role": "user", "content": "Test"}]
        response = await llm_client.generate_response(messages)

        assert response == "5xx retry success"
        assert llm_client.client.chat.completions.create.call_count == 2

    @pytest.mark.asyncio
    async def test_generate_response_5xx_error_retry_failure(self, llm_client):
        """Test 5xx error with failed retry."""
        # Create 5xx error
        mock_request = MagicMock()
        error = APIError(
            message="Internal server error", request=mock_request, body=None
        )
        error.status_code = 500

        llm_client.client.chat.completions.create = AsyncMock(side_effect=error)

        messages = [{"role": "user", "content": "Test"}]

        with pytest.raises(LLMAPIError):
            await llm_client.generate_response(messages)

    @pytest.mark.asyncio
    async def test_generate_response_4xx_error_no_retry(self, llm_client):
        """Test 4xx error (no retry)."""
        # Create 4xx error
        mock_request = MagicMock()
        error = APIError(message="Bad request", request=mock_request, body=None)
        error.status_code = 400

        llm_client.client.chat.completions.create = AsyncMock(side_effect=error)

        messages = [{"role": "user", "content": "Test"}]

        with pytest.raises(LLMAPIError):
            await llm_client.generate_response(messages)

    @pytest.mark.asyncio
    async def test_generate_response_retryable_generic_error_success(self, llm_client):
        """Test retryable generic error with successful retry."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Generic retry success"
        mock_response.usage = None

        llm_client.client.chat.completions.create = AsyncMock(
            side_effect=[
                Exception("Network error"),
                mock_response,
            ],
        )

        messages = [{"role": "user", "content": "Test"}]
        response = await llm_client.generate_response(messages)

        assert response == "Generic retry success"
        assert llm_client.client.chat.completions.create.call_count == 2

    @pytest.mark.asyncio
    async def test_generate_response_retryable_generic_error_failure(self, llm_client):
        """Test retryable generic error with failed retry."""
        llm_client.client.chat.completions.create = AsyncMock(
            side_effect=Exception("Network error"),
        )

        messages = [{"role": "user", "content": "Test"}]

        with pytest.raises(LLMError):
            await llm_client.generate_response(messages)

    @pytest.mark.asyncio
    async def test_generate_response_non_retryable_generic_error(self, llm_client):
        """Test non-retryable generic error."""
        llm_client.client.chat.completions.create = AsyncMock(
            side_effect=Exception("Invalid request format"),
        )

        messages = [{"role": "user", "content": "Test"}]

        with pytest.raises(LLMError):
            await llm_client.generate_response(messages)

    @pytest.mark.asyncio
    async def test_generate_response_empty_content(self, llm_client):
        """Test response with empty content."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = None  # Empty content
        mock_response.usage = None

        llm_client.client.chat.completions.create = AsyncMock(
            return_value=mock_response
        )

        messages = [{"role": "user", "content": "Test"}]
        response = await llm_client.generate_response(messages)

        assert response == ""

    @pytest.mark.asyncio
    async def test_generate_response_no_usage_info(self, llm_client):
        """Test response without usage information."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response without usage"
        mock_response.usage = None  # No usage info

        llm_client.client.chat.completions.create = AsyncMock(
            return_value=mock_response
        )

        messages = [{"role": "user", "content": "Test"}]
        response = await llm_client.generate_response(messages)

        assert response == "Response without usage"


class TestGlobalLLMClient:
    """Test cases for global LLM client."""

    def test_get_llm_client_singleton(self):
        """Test that get_llm_client returns singleton."""
        with patch("core.llm_client.get_settings") as mock_settings:
            mock_settings.return_value.openrouter_api_key = "test_key"
            mock_settings.return_value.openrouter_model = "test_model"
            mock_settings.return_value.llm_temperature = 0.9
            mock_settings.return_value.llm_max_tokens = 1000

            client1 = get_llm_client()
            client2 = get_llm_client()

            assert client1 is client2
            assert isinstance(client1, LLMClient)


class TestLLMErrorClasses:
    """Test cases for LLM error classes."""

    def test_llm_error_inheritance(self):
        """Test that LLM error classes inherit correctly."""
        assert issubclass(LLMTimeoutError, LLMError)
        assert issubclass(LLMRateLimitError, LLMError)
        assert issubclass(LLMConnectionError, LLMError)
        assert issubclass(LLMAPIError, LLMError)

    def test_llm_error_creation(self):
        """Test creating LLM error instances."""
        base_error = LLMError("Base error")
        timeout_error = LLMTimeoutError("Timeout")
        rate_limit_error = LLMRateLimitError("Rate limit")
        connection_error = LLMConnectionError("Connection failed")
        api_error = LLMAPIError("API error")

        assert str(base_error) == "Base error"
        assert str(timeout_error) == "Timeout"
        assert str(rate_limit_error) == "Rate limit"
        assert str(connection_error) == "Connection failed"
        assert str(api_error) == "API error"
