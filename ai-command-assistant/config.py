"""Application configuration and environment variable loading.
This module centralizes all runtime settings so secrets stay out of source code
and the rest of the application can consume a single, well-defined config object.
"""

from __future__ import annotations
import os
from dataclasses import dataclass

# Load values from a local .env file into the process environment during
# development. In production, real environment variables or a secrets
# manager should be used instead; loading .env is a convenience.
try:
    from dotenv import load_dotenv  # type: ignore

    load_dotenv()
except Exception:
    # If python-dotenv is not installed or .env is absent, continue — the
    # application will rely on real environment variables and validation
    # will fail early in `load_settings()` if required values are missing.
    pass


@dataclass(frozen=True)
class Settings:
    """Typed application settings loaded from environment variables.
    Keeping these values in a dataclass makes configuration explicit,
    discoverable, and easy to pass around without relying on global state.
    """

    api_key: str
    api_base_url: str
    model_name: str
    timeout_seconds: int = 30


def load_settings() -> Settings:
    """Load configuration from environment variables.
    Environment variables are used so secrets and deployment-specific values
    do not need to be hardcoded in the repository.
    """

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
        raise ValueError(
            "AI_TIMEOUT_SECONDS must be an integer value in seconds."
        ) from exc

    return Settings(
        api_key=key,
        api_base_url=base_url,
        model_name=m_name,
        timeout_seconds=timeout_value,
    )