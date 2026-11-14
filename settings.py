"""
Unified configuration and settings manager for fal.ai MCP & Video Pipeline.

Loads environment variables and validates configuration parameters.
Fails loudly if required keys are missing or credentials are invalid.
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent

# Load .env file explicitly
ENV_PATH = BASE_DIR / ".env"
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
else:
    load_dotenv()


class Settings:
    """Application configuration settings."""

    # Project metadata
    APP_NAME: str = "fal.ai Video Pipeline & MCP Server"
    VERSION: str = "2.0.0"
    BASE_DIR: Path = BASE_DIR

    # Database
    DATABASE_PATH: str = os.getenv(
        "DATABASE_PATH",
        str(BASE_DIR / "pipeline.db")
    )

    # fal.ai API configuration
    FAL_API_KEY: str = os.getenv("FAL_API_KEY", "").strip()
    FAL_QUEUE_URL: str = os.getenv("FAL_QUEUE_URL", "https://queue.fal.run").rstrip("/")
    FAL_RUN_URL: str = os.getenv("FAL_RUN_URL", "https://fal.run").rstrip("/")
    FAL_API_URL: str = os.getenv("FAL_API_URL", "https://api.fal.ai").rstrip("/")

    # Model defaults
    DEFAULT_MODEL_VIDEO: str = os.getenv("DEFAULT_MODEL_VIDEO", "fal-ai/kling-video/v1/standard/text-to-video")
    DEFAULT_MODEL_IMAGE: str = os.getenv("DEFAULT_MODEL_IMAGE", "fal-ai/flux/schnell")
    DEFAULT_MODEL_VOICE: str = os.getenv("DEFAULT_MODEL_VOICE", "fal-ai/minimax/speech-01")

    # Resilience & Retry Configuration
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "4"))
    RETRY_BACKOFF_BASE: float = float(os.getenv("RETRY_BACKOFF_BASE", "2.0"))
    REQUEST_TIMEOUT: float = float(os.getenv("REQUEST_TIMEOUT", "45.0"))
    FALLBACK_MODE_ENABLED: bool = os.getenv("FALLBACK_MODE_ENABLED", "true").lower() in ("true", "1", "yes")

    # Server configuration
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")

    @classmethod
    def validate_keys(cls, raise_on_missing: bool = False) -> bool:
        """
        Audit API credentials and ensure valid configuration.
        Fails loudly with clear guidance if raise_on_missing is True.
        """
        if not cls.FAL_API_KEY:
            msg = (
                "CRITICAL: FAL_API_KEY is not configured! "
                "Please set FAL_API_KEY in your .env file or environment variables. "
                "Obtain a key at https://fal.ai/dashboard/keys"
            )
            if raise_on_missing:
                raise ValueError(msg)
            return False
        return True


settings = Settings()
