"""Router for the /v1/capabilities endpoint."""

from __future__ import annotations

import time
import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.exceptions import CapabilityError
from app.schemas.capability import (
    CapabilityRequest,
    CapabilitySuccessResponse,
    CapabilityErrorResponse,
    ErrorDetail,
    ResponseMeta,
)
from app.services.capability_registry import get_registry

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/capabilities", tags=["capabilities"])


@router.post(
    "/run",
    response_model=CapabilitySuccessResponse,
    responses={
        400: {"model": CapabilityErrorResponse},
        404: {"model": CapabilityErrorResponse},
        422: {"model": CapabilityErrorResponse},
        502: {"model": CapabilityErrorResponse},
    },
    summary="Run a capability",
    description="Invoke a registered AI capability with the given input.",
)
async def run_capability(body: CapabilityRequest, request: Request) -> JSONResponse:
    """Execute the requested capability and return a unified response."""
    start = time.perf_counter()
    request_id = body.request_id or ""
    capability_name = body.capability

    try:
        registry = get_registry()
        data = await registry.run(capability_name, body.input)
        elapsed_ms = int((time.perf_counter() - start) * 1000)

        logger.info(
            "capability=%s request_id=%s elapsed_ms=%d status=ok",
            capability_name,
            request_id,
            elapsed_ms,
        )

        response = CapabilitySuccessResponse(
            data=data,
            meta=ResponseMeta(
                request_id=request_id,
                capability=capability_name,
                elapsed_ms=elapsed_ms,
            ),
        )
        return JSONResponse(content=response.model_dump(), status_code=200)

    except CapabilityError as exc:
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        logger.warning(
            "capability=%s request_id=%s elapsed_ms=%d status=error code=%s msg=%s",
            capability_name,
            request_id,
            elapsed_ms,
            exc.code,
            exc.message,
        )
        error_response = CapabilityErrorResponse(
            error=ErrorDetail(
                code=exc.code,
                message=exc.message,
                details=exc.details,
            ),
            meta=ResponseMeta(
                request_id=request_id,
                capability=capability_name,
                elapsed_ms=elapsed_ms,
            ),
        )
        return JSONResponse(
            content=error_response.model_dump(),
            status_code=exc.status_code,
        )

    except Exception as exc:
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        logger.exception(
            "capability=%s request_id=%s elapsed_ms=%d status=internal_error",
            capability_name,
            request_id,
            elapsed_ms,
        )
        error_response = CapabilityErrorResponse(
            error=ErrorDetail(
                code="INTERNAL_ERROR",
                message="An unexpected error occurred.",
                details={"error": str(exc)},
            ),
            meta=ResponseMeta(
                request_id=request_id,
                capability=capability_name,
                elapsed_ms=elapsed_ms,
            ),
        )
        return JSONResponse(
            content=error_response.model_dump(),
            status_code=500,
        )


@router.get(
    "/",
    summary="List capabilities",
    description="Return all registered capabilities and their descriptions.",
)
async def list_capabilities() -> dict:
    """List all available capabilities."""
    registry = get_registry()
    return {"capabilities": registry.list_capabilities()}

