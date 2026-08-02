"""AI client wrapper
Provides a single, well-documented `ask_ai` function that sends user input
to an LLM provider and returns the response text. The implementation is
provider-agnostic and defensive: it validates input, retries transient
failures, and normalizes different provider response shapes.
"""

from __future__ import annotations

import logging
import time
from typing import Any

import requests

from config import load_settings

logger = logging.getLogger(__name__)


class AiClientError(Exception):
	"""Raised when the AI client encounters an error the caller should see.
	This keeps provider-specific exceptions from leaking out of the module
	and provides a clear boundary for application-level error handling.
	"""


def _extract_text_from_response(data: Any) -> str | None:
	"""Try a few common response shapes to extract a human-readable text.
	Many LLM providers return slightly different JSON structures (for
	example `{"text": "..."}`, OpenAI-style `{"choices":[{"text": ...}]}`
	or chat-style `{"choices":[{"message": {"content": ...}}]}`).
	This helper makes best-effort extraction without assuming a single
	provider contract.
	"""

	# Simple top-level string
	if isinstance(data, str):
		return data.strip()

	# Dictionary-based responses
	if isinstance(data, dict):
		# common: {"text": "..."}
		text = data.get("text")
		if isinstance(text, str):
			return text.strip()

		# OpenAI-like: {"choices": [{"text": "..."}]}
		choices = data.get("choices")
		if isinstance(choices, list) and choices:
			first = choices[0]
			if isinstance(first, dict):
				# completions API
				if isinstance(first.get("text"), str):
					return first["text"].strip()
				# chat API
				msg = first.get("message") or first.get("delta")
				if isinstance(msg, dict):
					content = msg.get("content")
					if isinstance(content, str):
						return content.strip()

		# Anthropic-style or other: {"output": "..."} or {"result": "..."}
		for key in ("output", "result", "response"):
			val = data.get(key)
			if isinstance(val, str):
				return val.strip()

	# If nothing matched, None to indicate no usable text was found
	return None



def ask_ai(user_input: str) -> str | None:
	"""Send `user_input` to an LLM provider and return the response text.
	This function loads runtime settings from environment variables, sends a
	POST request with a conservative JSON payload, and returns the first
	usable text it can extract from the provider response.
	
	The function is defensive:
	- validates non-empty input
	- retries transient failures (network errors, 5xx, 429)
	- raises `AiClientError` with a clear message for caller handling

	Args:
		user_input: The user's question or prompt to send to the LLM.

	Returns:
		The textual response from the model, or None if no usable text is found.

	Raises:
		AiClientError: on configuration errors, network failures, or when
			the provider returns an unrecoverable error or an unexpected
			response shape.
	"""

	if not isinstance(user_input, str) or not user_input.strip():
		raise AiClientError("`user_input` must be a non-empty string")

	try:
		settings = load_settings()
	except Exception as exc:  # load_settings raises ValueError on missing config
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

		# Retry on server errors or rate limiting
		if resp.status_code >= 500 or resp.status_code == 429:
			logger.debug("Provider returned transient status %d", resp.status_code)
			if attempt == max_retries:
				raise AiClientError(
					f"AI provider error: HTTP {resp.status_code}"
				)
			time.sleep(backoff)
			backoff *= 2
			continue

		# Handle client errors immediately
		if resp.status_code >= 400:
			# try parse JSON error message
			msg = None
			try:
				err = resp.json()
				msg = err.get("error") or err.get("message") or str(err)
			except ValueError:
				msg = resp.text
			raise AiClientError(f"AI provider returned {resp.status_code}: {msg}")

		# Success: parse JSON
		try:
			data = resp.json()
		except ValueError as exc:
			raise AiClientError("Invalid JSON response from AI provider") from exc

		text = _extract_text_from_response(data)
		if text:
			return text
		
		# If parsing didn't yield text, raise a clear error
		raise AiClientError("AI response did not contain any usable text")
