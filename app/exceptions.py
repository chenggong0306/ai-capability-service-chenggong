"""Custom exceptions and global exception handlers for the capability service."""

from __future__ import annotations


class CapabilityError(Exception):
    """Base exception for capability-related errors."""

    def __init__(
        self,
        code: str,
        message: str,
        details: dict | None = None,
        status_code: int = 400,
    ) -> None:
        self.code = code
        self.message = message
        self.details = details or {}
        self.status_code = status_code
        super().__init__(message)


class CapabilityNotFoundError(CapabilityError):
    """Raised when the requested capability does not exist."""

    def __init__(self, capability: str) -> None:
        super().__init__(
            code="CAPABILITY_NOT_FOUND",
            message=f"Capability '{capability}' is not registered.",
            details={"capability": capability},
            status_code=404,
        )


class InvalidInputError(CapabilityError):
    """Raised when the input payload fails validation."""

    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(
            code="INVALID_INPUT",
            message=message,
            details=details or {},
            status_code=422,
        )


class ModelCallError(CapabilityError):
    """Raised when the underlying model call fails."""

    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(
            code="MODEL_CALL_FAILED",
            message=message,
            details=details or {},
            status_code=502,
        )

