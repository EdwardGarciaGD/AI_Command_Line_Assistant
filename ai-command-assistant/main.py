"""CLI entrypoint for the AI command-line assistant.
This module is intentionally thin: it handles user interaction (I/O)
and delegates all AI requests to `ask_ai` in `ai_client.py` so API logic
stays isolated from the application layer.
"""

from __future__ import annotations
import logging
from typing import NoReturn
from ai_client import ask_ai, AiClientError

logger = logging.getLogger(__name__)

def print_welcome():
    print("AI Command-Line Assistant")
    print("Type your question and press Enter. Type 'quit' or 'exit' to leave.")
    print()

def get_user_input() -> str:
    """Prompt the user and return the entered string (stripped).
    This function is simple and keeps input handling in one place so it can
    be changed easily for tests or different frontends.
    """

    return input("> ").strip()

def handle_query(query: str) -> None:
    """Send `query` to the AI client and print the response.
    This separates the application workflow from the lower-level client
    code and centralizes error handling for AI requests.
    """

    try:
        response = ask_ai(query)
    except AiClientError as exc:
        # Known client errors are shown to the user as friendly messages
        print(f"Error: {exc}")
        return
    except Exception as exc:  # pragma: no cover - last-resort safety
        # Unexpected errors are logged for debugging and reported generically
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
    """Exit the program cleanly.
    Separated into a function to make the main loop easier to read and to
    allow tests to patch this behavior if needed.
    """

    print("Goodbye!")
    raise SystemExit(0)

def main() -> int:
    """Main loop: welcome, prompt, delegate to the AI client, handle exit.
    Returns an integer exit code suitable for `sys.exit()`.
    """

    logging.basicConfig(level=logging.INFO)
    print_welcome()

    try:
        while True:
            try:
                query = get_user_input()
            except (KeyboardInterrupt, EOFError):
                # Handle Ctrl+C / Ctrl+D from the user as an intent to quit
                print()
                exit_gracefully()

            if not query:
                # Ignore empty input and keep prompting
                continue

            if query.lower() in ("quit", "exit", "q", "e"):
                exit_gracefully()

            handle_query(query)

    except SystemExit:
        return 0
    except Exception:
        # Top-level safety: log unexpected errors and exit non-zero
        logger.exception("Top-level exception in main loop")
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
