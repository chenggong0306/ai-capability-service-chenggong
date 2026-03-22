"""Sentiment analysis capability – mock & real model modes.

Supports multiple LLM providers (DeepSeek, Qwen, OpenAI) via the
OpenAI-compatible API interface.
"""

from __future__ import annotations

import logging
from typing import Any

from app.capabilities.base import BaseCapability
from app.config import get_settings
from app.exceptions import InvalidInputError, ModelCallError

logger = logging.getLogger(__name__)

# Simple keyword-based sentiment for mock mode
_POSITIVE_WORDS = {"good", "great", "excellent", "love", "happy", "wonderful", "best", "amazing", "fantastic", "awesome"}
_NEGATIVE_WORDS = {"bad", "terrible", "awful", "hate", "sad", "worst", "horrible", "poor", "ugly", "disappointing"}


class SentimentAnalysisCapability(BaseCapability):
    """Analyse the sentiment of a piece of text.

    * **Mock mode**: uses a simple keyword-counting heuristic.
    * **Real mode**: calls the configured LLM provider.
    """

    @property
    def name(self) -> str:
        return "sentiment_analysis"

    @property
    def description(self) -> str:
        return "Analyse text sentiment and return positive/negative/neutral with a confidence score."

    # ── validation ───────────────────────────────────────────────────────

    def validate_input(self, input_data: dict[str, Any]) -> None:
        if "text" not in input_data:
            raise InvalidInputError(
                "The 'text' field is required.",
                details={"missing_field": "text"},
            )
        if not isinstance(input_data["text"], str) or len(input_data["text"].strip()) == 0:
            raise InvalidInputError("The 'text' field must be a non-empty string.")

    # ── execution ────────────────────────────────────────────────────────

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        self.validate_input(input_data)

        settings = get_settings()
        text: str = input_data["text"]
        provider_name: str | None = input_data.get("provider")

        provider = settings.get_provider(provider_name)
        if provider is not None:
            return await self._call_llm(text, provider)
        return self._mock_sentiment(text)

    # ── private helpers ──────────────────────────────────────────────────

    @staticmethod
    def _mock_sentiment(text: str) -> dict[str, Any]:
        """Keyword-counting heuristic for mock mode."""
        logger.info("Using mock sentiment analysis.")
        words = set(text.lower().split())
        pos = len(words & _POSITIVE_WORDS)
        neg = len(words & _NEGATIVE_WORDS)
        total = pos + neg or 1

        if pos > neg:
            sentiment, confidence = "positive", round(pos / total, 2)
        elif neg > pos:
            sentiment, confidence = "negative", round(neg / total, 2)
        else:
            sentiment, confidence = "neutral", 0.5

        return {"result": {"sentiment": sentiment, "confidence": confidence}}

    @staticmethod
    async def _call_llm(text: str, provider) -> dict[str, Any]:  # noqa: ANN001
        """Call an OpenAI-compatible LLM for real sentiment analysis."""
        try:
            import openai
            from httpx import Timeout
        except ImportError as exc:
            raise ModelCallError(
                "The 'openai' package is required for real model calls. "
                "Install it with: pip install openai",
            ) from exc

        settings = get_settings()
        logger.info(
            "Calling provider=%s model=%s for sentiment_analysis.",
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
                            "Analyse the sentiment of the following text. "
                            'Respond ONLY with JSON: {"sentiment": "positive"|"negative"|"neutral", "confidence": 0.0-1.0}'
                        ),
                    },
                    {"role": "user", "content": text},
                ],
                temperature=0,
                max_tokens=60,
            )
            import json
            raw = response.choices[0].message.content.strip()
            parsed = json.loads(raw)
            return {"result": parsed}
        except (openai.OpenAIError, json.JSONDecodeError, KeyError) as exc:
            raise ModelCallError(
                f"Sentiment analysis model call failed ({provider.name}): {exc}",
                details={"provider": provider.name, "original_error": str(exc)},
            ) from exc

