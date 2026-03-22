"""FastAPI application entry-point."""

from __future__ import annotations

import logging
import sys

from fastapi import FastAPI

from app.config import get_settings
from app.middleware.logging import RequestLoggingMiddleware
from app.routers.capability import router as capability_router
from app.services.capability_registry import get_registry


def _configure_logging() -> None:
    """Set up structured console logging."""
    log_format = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
    logging.basicConfig(
        level=logging.DEBUG if get_settings().debug else logging.INFO,
        format=log_format,
        stream=sys.stdout,
    )


def create_app() -> FastAPI:
    """Application factory."""
    settings = get_settings()
    _configure_logging()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "A unified AI capability invocation service. "
            "Submit a capability name and input payload to run various AI tasks."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Middleware
    app.add_middleware(RequestLoggingMiddleware)

    # Routers
    app.include_router(capability_router)

    # Eagerly initialise the capability registry so errors surface at startup
    registry = get_registry()
    logging.getLogger(__name__).info(
        "Capabilities loaded: %s",
        [c["name"] for c in registry.list_capabilities()],
    )
    logging.getLogger(__name__).info(
        "Configured providers: %s  (default: %s)",
        settings.list_providers() or ["none (mock mode)"],
        settings.default_provider,
    )

    # Health-check
    @app.get("/health", tags=["ops"])
    async def health() -> dict:
        return {"status": "healthy", "version": settings.app_version}

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )

