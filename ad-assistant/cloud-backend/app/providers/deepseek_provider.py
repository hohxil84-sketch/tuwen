"""DeepSeekProvider — real AI Provider backed by DeepSeek Chat API.

Sprint-03 Task-02: first real :class:`AsyncProvider` implementation.

Uses the ``openai`` SDK with DeepSeek's OpenAI-compatible endpoint.
API key is read from ``settings.DEEPSEEK_API_KEY`` at init time and
never logged, stored in ``raw_usage``, or sent to the client.
"""

from __future__ import annotations

import logging

from openai import AsyncOpenAI

from app.core.config import settings
from app.providers.base import AsyncProvider, ProviderRequest, ProviderResult

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Provider-specific exception
# ---------------------------------------------------------------------------


class DeepSeekProviderError(Exception):
    """Controlled failure from DeepSeekProvider.

    ``error_code`` is a machine-readable short string (e.g. ``AUTH_ERROR``,
    ``RATE_LIMITED``, ``API_KEY_MISSING``).  ``message`` is a human-readable
    description suitable for server-side logging (not shown to end users).
    """

    def __init__(self, error_code: str, message: str) -> None:
        self.error_code = error_code
        self.message = message
        super().__init__(message)


# ---------------------------------------------------------------------------
# DeepSeekProvider
# ---------------------------------------------------------------------------


class DeepSeekProvider(AsyncProvider):
    """Real AI Provider that calls the DeepSeek Chat API.

    - provider name: ``"deepseek"``
    - model: configured via ``settings.DEEPSEEK_MODEL`` (default ``"deepseek-chat"``)
    - API key: ``settings.DEEPSEEK_API_KEY`` (must be set in ``.env``)
    - base URL: ``settings.DEEPSEEK_BASE_URL`` (default ``https://api.deepseek.com``)

    ``raw_usage`` records only safe metadata (model, finish_reason, usage
    token counts).  Raw prompt text, API key, and secrets are never written
    to ``raw_usage`` or logs.
    """

    PROVIDER_NAME = "deepseek"

    def __init__(self) -> None:
        self._model: str = settings.DEEPSEEK_MODEL
        self._client: AsyncOpenAI | None = None

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------

    async def call(self, request: ProviderRequest) -> ProviderResult:
        """Send *request.message* to DeepSeek and return a :class:`ProviderResult`.

        Raises:
            DeepSeekProviderError: on auth failure, rate limit, timeout,
                empty API key, or other controlled error conditions.
        """
        client = self._get_client()

        try:
            response = await client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": request.message}],
            )
        except Exception as exc:
            self._raise_mapped_error(exc)

        # Extract the first choice
        choice = response.choices[0] if response.choices else None
        if choice is None or not choice.message.content:
            raise DeepSeekProviderError(
                error_code="EMPTY_RESPONSE",
                message="DeepSeek returned no content in the response.",
            )

        # Extract usage
        usage = response.usage
        input_units = usage.prompt_tokens if usage else 0
        output_units = usage.completion_tokens if usage else 0

        # Build safe raw_usage — no prompt text, no API key
        raw_usage: dict = {
            "model": response.model or self._model,
            "finish_reason": choice.finish_reason or "unknown",
            "prompt_tokens": input_units,
            "completion_tokens": output_units,
            "total_tokens": usage.total_tokens if usage else 0,
        }

        return ProviderResult(
            provider=self.PROVIDER_NAME,
            model=self._model,
            input_units=input_units,
            output_units=output_units,
            image_units=0,
            gpu_seconds=0.0,
            raw_cost=0.0,  # estimated_cost calculated externally
            estimated_cost=0.0,
            currency="CNY",
            result={"text": choice.message.content},
            raw_usage=raw_usage,
        )

    # ------------------------------------------------------------------
    # internal helpers
    # ------------------------------------------------------------------

    def _get_client(self) -> AsyncOpenAI:
        """Return (or lazily create) the ``AsyncOpenAI`` client.

        Raises:
            DeepSeekProviderError: if ``DEEPSEEK_API_KEY`` is not configured.
        """
        if self._client is not None:
            return self._client

        api_key = settings.DEEPSEEK_API_KEY
        if not api_key:
            raise DeepSeekProviderError(
                error_code="API_KEY_MISSING",
                message="DEEPSEEK_API_KEY is not configured. Set it in .env.",
            )

        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url=settings.DEEPSEEK_BASE_URL,
        )
        return self._client

    @staticmethod
    def _raise_mapped_error(exc: Exception) -> None:
        """Map known SDK / network errors to :class:`DeepSeekProviderError`."""
        import openai

        # Auth errors (401, 403)
        if isinstance(exc, openai.AuthenticationError):
            raise DeepSeekProviderError(
                error_code="AUTH_ERROR",
                message="DeepSeek API key is invalid or expired.",
            ) from exc

        # Rate limit (429)
        if isinstance(exc, openai.RateLimitError):
            raise DeepSeekProviderError(
                error_code="RATE_LIMITED",
                message="DeepSeek rate limit exceeded — retry after backoff.",
            ) from exc

        # Timeout
        if isinstance(exc, openai.APITimeoutError):
            raise DeepSeekProviderError(
                error_code="TIMEOUT",
                message="DeepSeek API request timed out.",
            ) from exc

        # Connection error
        if isinstance(exc, openai.APIConnectionError):
            raise DeepSeekProviderError(
                error_code="CONNECTION_ERROR",
                message="Failed to connect to DeepSeek API.",
            ) from exc

        # Bad request (400) — likely prompt issue
        if isinstance(exc, openai.BadRequestError):
            raise DeepSeekProviderError(
                error_code="BAD_REQUEST",
                message=f"DeepSeek rejected the request: {exc}",
            ) from exc

        # Generic API error (500, etc.)
        if isinstance(exc, openai.APIStatusError):
            raise DeepSeekProviderError(
                error_code="API_ERROR",
                message=f"DeepSeek API error (status {exc.status_code}): {exc}",
            ) from exc

        # Unexpected — re-raise as generic provider error
        logger.exception("Unexpected error during DeepSeek API call")
        raise DeepSeekProviderError(
            error_code="UNKNOWN_ERROR",
            message=f"Unexpected DeepSeek error: {exc}",
        ) from exc
