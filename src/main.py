"""CLI entrypoint for the AI command-line assistant."""

from __future__ import annotations

import logging
from typing import NoReturn

from .ai_client import AiClientError, ask_ai

logger = logging.getLogger(__name__)


def print_welcome() -> None:
    print("AI Command-Line Assistant")
    print("Type your question and press Enter. Type 'quit' or 'exit' to leave.")
    print()


def get_user_input() -> str:
    """Prompt the user and return stripped input."""

    return input("> ").strip()


def handle_query(query: str) -> None:
    """Send query to AI and print the response with safe error handling."""

    try:
        response = ask_ai(query)
    except AiClientError as exc:
        print(f"Error: {exc}")
        return
    except Exception:
        logger.exception("Unexpected error while asking AI")
        print("An unexpected error occurred. Please try again.")
        return

    if response is None:
        print("No response received from the AI.")
    else:
        print()
        print(response)
        print()


def exit_gracefully() -> NoReturn:
    """Exit the program cleanly."""

    print("Goodbye!")
    raise SystemExit(0)


def main() -> int:
    """Run the CLI loop and return process exit code."""

    logging.basicConfig(level=logging.INFO)
    print_welcome()

    try:
        while True:
            try:
                query = get_user_input()
            except (KeyboardInterrupt, EOFError):
                print()
                exit_gracefully()

            if not query:
                continue

            if query.lower() in ("quit", "exit", "q", "e"):
                exit_gracefully()

            handle_query(query)

    except SystemExit:
        return 0
    except Exception:
        logger.exception("Top-level exception in main loop")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
