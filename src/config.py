"""Application configuration and environment variable loading.
This module centralizes runtime settings so secrets stay out of source code.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

# Load values from a local .env file during development.
try:
    from dotenv import load_dotenv  # type: ignore

    load_dotenv()
except Exception:
    # If python-dotenv is unavailable, rely on real env vars.
    pass


@dataclass(frozen=True)
class Settings:
    """Typed application settings loaded from environment variables."""

    api_key: str
    api_base_url: str
    model_name: str
    timeout_seconds: int = 30


def load_settings() -> Settings:
    """Load and validate required configuration from environment variables."""

    key = os.getenv("AI_API_KEY")
    base_url = os.getenv("AI_API_BASE_URL")
    m_name = os.getenv("AI_MODEL_NAME")
    seconds = os.getenv("AI_TIMEOUT_SECONDS", "30")

    if not key:
        raise ValueError("Missing required environment variable: AI_API_KEY")

    if not base_url:
        raise ValueError("Missing required environment variable: AI_API_BASE_URL")

    if not m_name:
        raise ValueError("Missing required environment variable: AI_MODEL_NAME")

    try:
        timeout_value = int(seconds)
    except ValueError as exc:
        raise ValueError("AI_TIMEOUT_SECONDS must be an integer value in seconds.") from exc

    return Settings(
        api_key=key,
        api_base_url=base_url,
        model_name=m_name,
        timeout_seconds=timeout_value,
    )
