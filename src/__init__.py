"""Top-level package for the AI Command-Line Assistant.

This package exposes the primary modules so callers can import via:
- from src import main
- from src import ai_client
- from src import config
"""

from . import ai_client, config, main

__all__ = ["ai_client", "config", "main"]
