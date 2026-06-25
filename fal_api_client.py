"""
fal.ai API client for async HTTP communication.

Uses the fal.ai queue API at https://queue.fal.run.
Model IDs look like: fal-ai/flux/schnell, fal-ai/whisper, etc.
"""

import os
import json
import httpx
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv


# ============================================================================
# Configuration
# ============================================================================

# Load .env from the project directory regardless of the launch cwd
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

FAL_API_KEY = os.environ.get("FAL_API_KEY", "")
FAL_QUEUE_URL = "https://queue.fal.run"
FAL_RUN_URL = "https://fal.run"

DEFAULT_TIMEOUT = 30.0


# ============================================================================
# Error Handling
# ============================================================================


class FalAPIError(Exception):
    pass


class FalAuthenticationError(FalAPIError):
    pass


def _handle_api_error(e: Exception, response_text: str = "") -> str:
    if isinstance(e, httpx.HTTPStatusError):
        status = e.response.status_code
        if status == 401:
            return (
                "Authentication failed. Check that FAL_API_KEY is set correctly. "
                "Get your key from https://fal.ai/dashboard/keys"
            )
        elif status == 403:
            return "Permission denied. Your API key may not have access to this resource."
        elif status == 404:
            return (
                "Not found. Verify the application ID is correct. "
                "Example IDs: fal-ai/flux/schnell, fal-ai/flux/dev, fal-ai/whisper"
            )
        elif status == 429:
            return "Rate limit exceeded. Wait a moment before retrying."
        else:
            detail = ""
            if response_text:
                try:
                    data = json.loads(response_text)
                    if isinstance(data, dict):
                        detail = data.get("detail", data.get("error", str(data)))[:200]
                except json.JSONDecodeError:
                    detail = response_text[:200]
            return f"API request failed with status {status}. {detail}"

    elif isinstance(e, httpx.TimeoutException):
        return "Request timed out. Use poll_job_status with the request_id to check progress."

    elif isinstance(e, httpx.ConnectError):
        return "Could not connect to fal.ai. Check your internet connection."

    return f"Unexpected error: {type(e).__name__}: {e}"


# ============================================================================
# HTTP Client
# ============================================================================


def _make_client(base_url: str) -> httpx.AsyncClient:
    if not FAL_API_KEY:
        raise FalAuthenticationError(
            "FAL_API_KEY environment variable is not set. "
            "Get your key from https://fal.ai/dashboard/keys"
        )
    return httpx.AsyncClient(
        base_url=base_url,
        headers={"Authorization": f"Key {FAL_API_KEY}"},
        timeout=DEFAULT_TIMEOUT,
    )


# ============================================================================
# API Operations
# ============================================================================

# Curated list of popular fal.ai models
POPULAR_MODELS = [
    {"id": "fal-ai/flux/schnell", "name": "FLUX.1 Schnell", "description": "Fast text-to-image, 4 steps, Apache 2.0"},
    {"id": "fal-ai/flux/dev", "name": "FLUX.1 Dev", "description": "High quality text-to-image, 28 steps"},
    {"id": "fal-ai/flux-pro", "name": "FLUX.1 Pro", "description": "Professional text-to-image, highest quality"},
    {"id": "fal-ai/flux/pro/ultra", "name": "FLUX.1 Pro Ultra", "description": "Highest resolution text-to-image (up to 4MP)"},
    {"id": "fal-ai/flux-lora", "name": "FLUX LoRA", "description": "Text-to-image with custom LoRA weights"},
    {"id": "fal-ai/stable-diffusion-v3-medium", "name": "Stable Diffusion 3 Medium", "description": "SD3 text-to-image"},
    {"id": "fal-ai/aura-flow", "name": "AuraFlow", "description": "Open-source text-to-image flow model"},
    {"id": "fal-ai/stable-video", "name": "Stable Video Diffusion", "description": "Image-to-video generation"},
    {"id": "fal-ai/wan/v2.1/1.3b", "name": "Wan 2.1 1.3B", "description": "Fast video generation model"},
    {"id": "fal-ai/wan/v2.1/14b", "name": "Wan 2.1 14B", "description": "High quality video generation model"},
    {"id": "fal-ai/whisper", "name": "Whisper", "description": "OpenAI Whisper speech-to-text transcription"},
    {"id": "fal-ai/imageutils/rembg", "name": "Background Removal", "description": "Remove image backgrounds"},
    {"id": "fal-ai/face-swap", "name": "Face Swap", "description": "Swap faces between images"},
    {"id": "fal-ai/pulid", "name": "PuLID", "description": "Identity-preserving image generation"},
    {"id": "fal-ai/controlnet-sdxl", "name": "ControlNet SDXL", "description": "Controlled image generation with SDXL"},
    {"id": "fal-ai/lora", "name": "Stable Diffusion + LoRA", "description": "SD image generation with LoRA weights"},
    {"id": "fal-ai/clarity-upscaler", "name": "Clarity Upscaler", "description": "High-quality image upscaling"},
    {"id": "fal-ai/esrgan", "name": "ESRGAN", "description": "Enhanced Super-Resolution image upscaling"},
    {"id": "fal-ai/kokoro", "name": "Kokoro TTS", "description": "Text-to-speech synthesis"},
    {"id": "fal-ai/llava-next", "name": "LLaVA-NeXT", "description": "Vision-language model for image understanding"},
]


async def list_applications(
    limit: int = 20,
    offset: int = 0,
    search: Optional[str] = None,
) -> Dict[str, Any]:
    models = POPULAR_MODELS
    if search:
        q = search.lower()
        models = [m for m in models if q in m["id"].lower() or q in m["name"].lower() or q in m["description"].lower()]
    total = len(models)
    page = models[offset: offset + limit]
    return {
        "applications": page,
        "total": total,
        "limit": limit,
        "offset": offset,
        "note": "This is a curated list of popular models. Browse all models at https://fal.ai/models",
    }


async def get_application(application_id: str) -> Dict[str, Any]:
    """Fetch the OpenAPI schema for an application."""
    async with _make_client(FAL_RUN_URL) as client:
        try:
            response = await client.get(f"/{application_id}/openapi.json")
            response.raise_for_status()
            schema = response.json()
            return {
                "application_id": application_id,
                "openapi_schema": schema,
                "submit_url": f"{FAL_QUEUE_URL}/{application_id}",
            }
        except Exception as e:
            raise FalAPIError(_handle_api_error(e, e.response.text if hasattr(e, "response") else ""))


async def submit_job(
    application_id: str,
    input_data: Dict[str, Any],
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    async with _make_client(FAL_QUEUE_URL) as client:
        try:
            payload = dict(input_data)
            if request_id:
                payload["request_id"] = request_id

            response = await client.post(f"/{application_id}", json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise FalAPIError(_handle_api_error(e, e.response.text if hasattr(e, "response") else ""))


async def poll_job_status(status_url: str) -> Dict[str, Any]:
    """Poll status using the status_url returned by submit_job."""
    async with httpx.AsyncClient(
        headers={"Authorization": f"Key {FAL_API_KEY}", "User-Agent": "fal-mcp/1.0"},
        timeout=DEFAULT_TIMEOUT,
    ) as client:
        try:
            response = await client.get(status_url, params={"logs": "1"})
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise FalAPIError(_handle_api_error(e, e.response.text if hasattr(e, "response") else ""))


async def get_job_result(response_url: str) -> Dict[str, Any]:
    """Get job result using the response_url returned by submit_job."""
    async with httpx.AsyncClient(
        headers={"Authorization": f"Key {FAL_API_KEY}", "User-Agent": "fal-mcp/1.0"},
        timeout=DEFAULT_TIMEOUT,
    ) as client:
        try:
            response = await client.get(response_url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise FalAPIError(_handle_api_error(e, e.response.text if hasattr(e, "response") else ""))


async def list_queue_items(
    application_id: str,
    limit: int = 20,
    offset: int = 0,
    status: Optional[str] = None,
) -> Dict[str, Any]:
    return {
        "note": "fal.ai does not expose a queue listing API. Use poll_job_status with a specific request_id to check job status.",
        "application_id": application_id,
    }


async def cancel_job(cancel_url: str) -> Dict[str, Any]:
    """Cancel a job using the cancel_url returned by submit_job."""
    async with httpx.AsyncClient(
        headers={"Authorization": f"Key {FAL_API_KEY}", "User-Agent": "fal-mcp/1.0"},
        timeout=DEFAULT_TIMEOUT,
    ) as client:
        try:
            response = await client.put(cancel_url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise FalAPIError(_handle_api_error(e, e.response.text if hasattr(e, "response") else ""))


async def get_account_info() -> Dict[str, Any]:
    return {
        "note": "fal.ai does not expose an account info REST endpoint. View your account at https://fal.ai/dashboard",
        "api_key_configured": bool(FAL_API_KEY),
    }


async def get_usage_stats(days: int = 7) -> Dict[str, Any]:
    return {
        "note": "fal.ai does not expose a usage stats REST endpoint. View usage at https://fal.ai/dashboard",
        "api_key_configured": bool(FAL_API_KEY),
    }
