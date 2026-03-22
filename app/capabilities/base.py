"""Abstract base class for all capabilities."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseCapability(ABC):
    """Every capability must subclass this and implement `execute`.

    This enables a plugin-style architecture:
    1. Inherit from BaseCapability.
    2. Implement `name` (property) and `execute`.
    3. Register the instance in the CapabilityRegistry.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this capability (e.g. 'text_summary')."""

    @property
    def description(self) -> str:
        """Human-readable description (optional override)."""
        return ""

    @abstractmethod
    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Run the capability and return a result dict.

        Parameters
        ----------
        input_data:
            The ``input`` field from the incoming request.

        Returns
        -------
        dict[str, Any]
            Must contain at least ``{"result": ...}``.

        Raises
        ------
        InvalidInputError
            If the input payload is malformed.
        ModelCallError
            If the underlying model/API call fails.
        """

    def validate_input(self, input_data: dict[str, Any]) -> None:
        """Optional hook to validate input before execution.

        Override in subclasses to add custom validation.
        Raise ``InvalidInputError`` on failures.
        """

