"""AI client wrapper.

Provides a defensive `ask_ai` function that validates input, retries transient
errors, and normalizes common provider response shapes.
"""

from __future__ import annotations

import logging
import time
from typing import Any

import requests

from .config import load_settings

logger = logging.getLogger(__name__)


class AiClientError(Exception):
    """Raised when the AI client encounters an error the caller should see."""


def _extract_text_from_response(data: Any) -> str | None:
    """Best-effort extraction from common LLM JSON response shapes."""

    if isinstance(data, str):
        return data.strip()

    if isinstance(data, dict):
        text = data.get("text")
        if isinstance(text, str):
            return text.strip()

        choices = data.get("choices")
        if isinstance(choices, list) and choices:
            first = choices[0]
            if isinstance(first, dict):
                if isinstance(first.get("text"), str):
                    return first["text"].strip()
                msg = first.get("message") or first.get("delta")
                if isinstance(msg, dict):
                    content = msg.get("content")
                    if isinstance(content, str):
                        return content.strip()

        for key in ("output", "result", "response"):
            val = data.get(key)
            if isinstance(val, str):
                return val.strip()

    return None


def ask_ai(user_input: str) -> str | None:
    """Send user input to the provider and return extracted response text."""

    if not isinstance(user_input, str) or not user_input.strip():
        raise AiClientError("`user_input` must be a non-empty string")

    try:
        settings = load_settings()
    except Exception as exc:
        raise AiClientError("Failed to load configuration") from exc

    url = settings.api_base_url
    headers = {
        "Authorization": f"Bearer {settings.api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    payload = {"model": settings.model_name, "prompt": user_input}

    max_retries = 3
    backoff = 1.0

    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.post(
                url, json=payload, headers=headers, timeout=settings.timeout_seconds
            )
        except requests.RequestException as exc:
            logger.debug("Network error on attempt %d: %s", attempt, exc)
            if attempt == max_retries:
                raise AiClientError("Network error while contacting AI provider") from exc
            time.sleep(backoff)
            backoff *= 2
            continue

        if resp.status_code >= 500 or resp.status_code == 429:
            logger.debug("Provider returned transient status %d", resp.status_code)
            if attempt == max_retries:
                raise AiClientError(f"AI provider error: HTTP {resp.status_code}")
            time.sleep(backoff)
            backoff *= 2
            continue

        if resp.status_code >= 400:
            try:
                err = resp.json()
                msg = err.get("error") or err.get("message") or str(err)
            except ValueError:
                msg = resp.text
            raise AiClientError(f"AI provider returned {resp.status_code}: {msg}")

        try:
            data = resp.json()
        except ValueError as exc:
            raise AiClientError("Invalid JSON response from AI provider") from exc

        text = _extract_text_from_response(data)
        if text:
            return text

        raise AiClientError("AI response did not contain any usable text")

    return None
