"""
ASGI Web Server & REST API for fal.ai Video Pipeline Command Center.

Serves the single-page glassmorphic dashboard frontend and manages asynchronous
job dispatching, SQLite state tracking, and background pipeline execution.
"""

import argparse
import asyncio
import json
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional

import uvicorn
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import FileResponse, JSONResponse, Response
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

import db
import pipeline
from settings import settings

logger = logging.getLogger("server")
logging.basicConfig(level=logging.INFO)

STATIC_DIR = Path(__file__).parent / "static"


# ============================================================================
# API Route Handlers
# ============================================================================

async def handle_index(request: Request) -> Response:
    """Serve the single-page application dashboard HTML."""
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        return JSONResponse({"error": "Dashboard static files not found"}, status_code=404)
    return FileResponse(index_file)


async def handle_list_jobs(request: Request) -> JSONResponse:
    """List jobs with optional status filtering and search query."""
    status = request.query_params.get("status")
    search = request.query_params.get("search")
    limit = int(request.query_params.get("limit", "50"))
    offset = int(request.query_params.get("offset", "0"))

    jobs = await db.list_jobs(status=status, search=search, limit=limit, offset=offset)
    return JSONResponse(jobs)


async def handle_get_job(request: Request) -> JSONResponse:
    """Get single job record by ID."""
    job_id = request.path_params["job_id"]
    job = await db.get_job(job_id)
    if not job:
        return JSONResponse({"error": f"Job '{job_id}' not found"}, status_code=404)
    return JSONResponse(job)


async def handle_create_job(request: Request) -> JSONResponse:
    """Create a new video generation job and launch async pipeline execution."""
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON body"}, status_code=400)

    job_data = {
        "title": body.get("title", "Untitled Production"),
        "niche": body.get("niche", "Sci-Fi Lore"),
        "focus_keyword": body.get("focus_keyword"),
        "visual_style": body.get("visual_style", "Cinematic Photorealism"),
        "target_duration_sec": int(body.get("target_duration_sec", 60)),
        "full_script": body.get("full_script"),
        "recap_intro": body.get("recap_intro"),
        "custom_cliffhanger": body.get("custom_cliffhanger"),
        "target_demographic": body.get("target_demographic", "General Audience"),
        "voice_tone": body.get("voice_tone", "Cinematic Narrator"),
        "model_id": body.get("model_id") or settings.DEFAULT_MODEL_VIDEO,
        "status": "QUEUED"
    }

    created = await db.create_job(job_data)
    job_id = created["id"]

    # Launch pipeline asynchronously in the background
    asyncio.create_task(pipeline.run_video_pipeline(job_id))

    return JSONResponse(created, status_code=201)


async def handle_retry_job(request: Request) -> JSONResponse:
    """Restart video production for a specified job."""
    job_id = request.path_params["job_id"]
    job = await db.get_job(job_id)
    if not job:
        return JSONResponse({"error": f"Job '{job_id}' not found"}, status_code=404)

    await db.update_job(job_id, {"status": "QUEUED", "error_log": None})
    asyncio.create_task(pipeline.run_video_pipeline(job_id))

    updated = await db.get_job(job_id)
    return JSONResponse(updated)


async def handle_get_models(request: Request) -> JSONResponse:
    """Return catalog of featured fal.ai video and media models."""
    models = [
        {
            "id": "fal-ai/kling-video/v1/standard/text-to-video",
            "name": "Kling Video Standard",
            "category": "Video Generation",
            "description": "High physical coherence, dynamic motion, and photorealistic texture detail."
        },
        {
            "id": "fal-ai/minimax/video-01",
            "name": "Minimax Video-01",
            "category": "Video Generation",
            "description": "Cinematic pacing, crisp lighting, and expressive camera dynamics."
        },
        {
            "id": "fal-ai/luma-dream-machine",
            "name": "Luma Dream Machine",
            "category": "Video Generation",
            "description": "Smooth camera moves, 3D spatial consistency, and realistic lighting."
        },
        {
            "id": "fal-ai/cogvideox-5b",
            "name": "CogVideoX 5B",
            "category": "Video Generation",
            "description": "Open-weight video foundation model with surrealistic flair."
        },
        {
            "id": "fal-ai/flux/schnell",
            "name": "Flux Schnell",
            "category": "Image Generation",
            "description": "Ultra-fast high-definition visual generation for storyboarding and title cards."
        }
    ]
    return JSONResponse({"models": models})


async def handle_health_check(request: Request) -> JSONResponse:
    """System health check and configuration audit."""
    api_key_configured = bool(settings.FAL_API_KEY and not settings.FAL_API_KEY.startswith("your-api-key"))
    return JSONResponse({
        "status": "HEALTHY",
        "app_name": settings.APP_NAME,
        "version": settings.VERSION,
        "api_key_configured": api_key_configured,
        "fallback_mode_enabled": settings.FALLBACK_MODE_ENABLED,
        "database_path": settings.DATABASE_PATH,
        "default_model": settings.DEFAULT_MODEL_VIDEO
    })


# ============================================================================
# Application Lifecycle & Routing
# ============================================================================

@asynccontextmanager
async def lifespan(app: Starlette):
    """Initialize database and schema migrations on application startup."""
    logger.info("Initializing database migrations...")
    await db.init_db()
    logger.info(f"fal.ai Video Pipeline server starting up. Database ready at {settings.DATABASE_PATH}")
    yield


routes = [
    Route("/", endpoint=handle_index, methods=["GET"]),
    Route("/api/jobs", endpoint=handle_list_jobs, methods=["GET"]),
    Route("/api/jobs", endpoint=handle_create_job, methods=["POST"]),
    Route("/api/jobs/{job_id}", endpoint=handle_get_job, methods=["GET"]),
    Route("/api/jobs/{job_id}/retry", endpoint=handle_retry_job, methods=["POST"]),
    Route("/api/models", endpoint=handle_get_models, methods=["GET"]),
    Route("/api/health", endpoint=handle_health_check, methods=["GET"]),
    Mount("/static", app=StaticFiles(directory=str(STATIC_DIR)), name="static"),
]

middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
]

app = Starlette(
    debug=settings.DEBUG,
    routes=routes,
    middleware=middleware,
    lifespan=lifespan
)


def main():
    parser = argparse.ArgumentParser(description="fal.ai Video Pipeline Server")
    parser.add_argument("--host", default=settings.HOST, help="Host to bind (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=settings.PORT, help="Port to bind (default: 8000)")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    args = parser.parse_args()

    uvicorn.run("server:app", host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()
