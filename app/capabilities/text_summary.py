"""Text summarisation capability – mock & real model modes.

Supports multiple LLM providers (DeepSeek, Qwen, OpenAI) via the
OpenAI-compatible API interface.  The caller can optionally specify
a ``provider`` in the input to override the default.
"""

from __future__ import annotations

import logging
from typing import Any

from app.capabilities.base import BaseCapability
from app.config import get_settings
from app.exceptions import InvalidInputError, ModelCallError

logger = logging.getLogger(__name__)


class TextSummaryCapability(BaseCapability):
    """Summarise a piece of text.

    * **Mock mode** (default): truncates the text to ``max_length`` as a
      simple simulation.
    * **Real mode**: calls the configured LLM provider (DeepSeek / Qwen /
      OpenAI) through the OpenAI-compatible API.
    """

    @property
    def name(self) -> str:
        return "text_summary"

    @property
    def description(self) -> str:
        return "Summarise a piece of text into a shorter version."

    # ── validation ───────────────────────────────────────────────────────

    def validate_input(self, input_data: dict[str, Any]) -> None:
        if "text" not in input_data:
            raise InvalidInputError(
                "The 'text' field is required.",
                details={"missing_field": "text"},
            )
        if not isinstance(input_data["text"], str) or len(input_data["text"].strip()) == 0:
            raise InvalidInputError("The 'text' field must be a non-empty string.")

        max_length = input_data.get("max_length")
        if max_length is not None and (not isinstance(max_length, int) or max_length <= 0):
            raise InvalidInputError("'max_length' must be a positive integer.")

    # ── execution ────────────────────────────────────────────────────────

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        self.validate_input(input_data)

        settings = get_settings()
        text: str = input_data["text"]
        max_length: int = input_data.get("max_length", settings.default_summary_max_length)
        provider_name: str | None = input_data.get("provider")

        provider = settings.get_provider(provider_name)
        if provider is not None:
            result = await self._call_llm(text, max_length, provider)
        else:
            result = self._mock_summary(text, max_length)

        return {"result": result}

    # ── private helpers ──────────────────────────────────────────────────

    @staticmethod
    def _mock_summary(text: str, max_length: int) -> str:
        """Simple mock: return the first *max_length* characters + ellipsis."""
        logger.info("Using mock summarisation (no API key configured).")
        if len(text) <= max_length:
            return text
        return text[:max_length].rsplit(" ", 1)[0] + "..."

    @staticmethod
    async def _call_llm(text: str, max_length: int, provider) -> str:  # noqa: ANN001
        """Call an OpenAI-compatible LLM provider for a real summary."""
        try:
            import openai  # lazy import – optional dependency
            from httpx import Timeout
        except ImportError as exc:
            raise ModelCallError(
                "The 'openai' package is required for real model calls. "
                "Install it with: pip install openai",
            ) from exc

        settings = get_settings()
        logger.info(
            "Calling provider=%s model=%s for text_summary.",
            provider.name,
            provider.model,
        )
        client = openai.AsyncOpenAI(
            api_key=provider.api_key,
            base_url=provider.base_url,
            timeout=Timeout(settings.llm_timeout, connect=10.0),
            max_retries=settings.llm_max_retries,
        )

        try:
            response = await client.chat.completions.create(
                model=provider.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            f"Summarise the following text in at most {max_length} characters. "
                            "Return only the summary, nothing else."
                        ),
                    },
                    {"role": "user", "content": text},
                ],
                temperature=0.3,
                max_tokens=max_length,
            )
            return response.choices[0].message.content.strip()
        except openai.OpenAIError as exc:
            raise ModelCallError(
                f"LLM API call failed ({provider.name}): {exc}",
                details={"provider": provider.name, "original_error": str(exc)},
            ) from exc

