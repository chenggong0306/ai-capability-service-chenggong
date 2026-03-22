"""Capability registry – central hub for discovering and invoking capabilities."""

from __future__ import annotations

import logging
from typing import Any

from app.capabilities.base import BaseCapability
from app.exceptions import CapabilityNotFoundError

logger = logging.getLogger(__name__)


class CapabilityRegistry:
    """Thread-safe registry that maps capability names to their implementations.

    Usage::

        registry = CapabilityRegistry()
        registry.register(TextSummaryCapability())
        result = await registry.run("text_summary", {"text": "..."})
    """

    def __init__(self) -> None:
        self._capabilities: dict[str, BaseCapability] = {}

    def register(self, capability: BaseCapability) -> None:
        """Register a capability instance."""
        logger.info("Registered capability: %s", capability.name)
        self._capabilities[capability.name] = capability

    def get(self, name: str) -> BaseCapability:
        """Look up a capability by name; raises if not found."""
        cap = self._capabilities.get(name)
        if cap is None:
            raise CapabilityNotFoundError(name)
        return cap

    async def run(self, name: str, input_data: dict[str, Any]) -> dict[str, Any]:
        """Look up and execute a capability."""
        capability = self.get(name)
        return await capability.execute(input_data)

    def list_capabilities(self) -> list[dict[str, str]]:
        """Return metadata for all registered capabilities."""
        return [
            {"name": cap.name, "description": cap.description}
            for cap in self._capabilities.values()
        ]


# ── module-level singleton ───────────────────────────────────────────────────

_registry: CapabilityRegistry | None = None


def get_registry() -> CapabilityRegistry:
    """Return the global registry, creating it on first call."""
    global _registry  # noqa: PLW0603
    if _registry is None:
        _registry = _create_default_registry()
    return _registry


def _create_default_registry() -> CapabilityRegistry:
    """Build the default registry with all built-in capabilities."""
    from app.capabilities.text_summary import TextSummaryCapability
    from app.capabilities.sentiment_analysis import SentimentAnalysisCapability

    registry = CapabilityRegistry()
    registry.register(TextSummaryCapability())
    registry.register(SentimentAnalysisCapability())
    return registry

