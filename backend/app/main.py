"""FastAPI application entry point with lifespan, CORS, and static file serving."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.app.config import settings
from backend.app.services.nebius_client import nebius_client
from backend.app.routers.factcheck import router as factcheck_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: validate keys, discover models. Shutdown: clean up."""
    logger.info("=" * 60)
    logger.info("FactCheck Radar starting up...")
    logger.info("=" * 60)

    # Check API keys
    if not settings.nebius_api_key:
        logger.error("⚠️  NEBIUS_API_KEY is not set! LLM calls will fail.")
    else:
        logger.info("✅ NEBIUS_API_KEY is configured")

    if not settings.tavily_api_key:
        logger.error("⚠️  TAVILY_API_KEY is not set! Web search will fail.")
    else:
        logger.info("✅ TAVILY_API_KEY is configured")

    # Discover available models
    logger.info("Discovering models on Nebius Token Factory...")
    await nebius_client.discover_models()
    logger.info("Fast model: %s", nebius_client.fast_model)
    logger.info("Reasoning model: %s", nebius_client.reasoning_model)

    logger.info("=" * 60)
    logger.info("FactCheck Radar ready! http://localhost:8000")
    logger.info("=" * 60)

    yield

    logger.info("FactCheck Radar shutting down...")


# Create app
app = FastAPI(
    title="FactCheck Radar",
    description="AI-powered fact-checking agent using NVIDIA Nemotron via Nebius Token Factory",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow frontend dev server and production origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:8000",  # Production (same origin)
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(factcheck_router)


# Health check
@app.get("/api/health")
async def health():
    """Health check endpoint returning model availability."""
    return {
        "status": "ok",
        "models": {
            "fast": nebius_client.fast_model,
            "reasoning": nebius_client.reasoning_model,
        },
        "api_keys": {
            "nebius": bool(settings.nebius_api_key),
            "tavily": bool(settings.tavily_api_key),
        },
    }


# Serve frontend static files in production
FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"

if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        """Serve the frontend SPA for any non-API route with path traversal protection."""
        resolved_dist = FRONTEND_DIST.resolve()
        file_path = (FRONTEND_DIST / full_path).resolve()
        if file_path.is_relative_to(resolved_dist) and file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(resolved_dist / "index.html")
