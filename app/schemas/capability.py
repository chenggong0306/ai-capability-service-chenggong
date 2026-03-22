"""Pydantic schemas for the capability API."""

from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, Field


# ── Request ──────────────────────────────────────────────────────────────────

class CapabilityRequest(BaseModel):
    """Incoming request for /v1/capabilities/run."""

    capability: str = Field(
        ...,
        description="Name of the capability to invoke, e.g. 'text_summary'.",
        examples=["text_summary"],
    )
    input: dict[str, Any] = Field(
        ...,
        description="Capability-specific input payload.",
        examples=[{"text": "Long text content...", "max_length": 120}],
    )
    request_id: str | None = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Optional client-supplied request identifier.",
    )


# ── Response ─────────────────────────────────────────────────────────────────

class ResponseMeta(BaseModel):
    """Metadata block shared by success and error responses."""

    request_id: str
    capability: str
    elapsed_ms: int


class CapabilitySuccessResponse(BaseModel):
    """Successful response envelope."""

    ok: bool = True
    data: dict[str, Any]
    meta: ResponseMeta


class ErrorDetail(BaseModel):
    """Error detail block."""

    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class CapabilityErrorResponse(BaseModel):
    """Error response envelope."""

    ok: bool = False
    error: ErrorDetail
    meta: ResponseMeta

