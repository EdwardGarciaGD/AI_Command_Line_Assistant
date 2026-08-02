"""Unit tests for the CLI loop in `main.py`.

These tests patch `input()` and `ai_client.ask_ai` to avoid network usage
and to exercise different success and error paths. Each test includes a
brief comment explaining possible exceptions and recommended fixes.
"""

import builtins
import pytest

from ai_client import AiClientError
import main


def test_quit_immediately(monkeypatch):
    """If the user immediately types 'quit' the program exits with code 0.

    Possible exceptions:
    - If `input` is not patched correctly, the test may hang waiting for
      stdin. Ensure tests patch `builtins.input` or run in a headless mode.
    """

    inputs = iter(["quit"])
    monkeypatch.setattr(builtins, "input", lambda prompt="": next(inputs))

    rc = main.main()
    assert rc == 0


def test_handle_query_success(monkeypatch, capsys):
    """Valid query is sent to `ask_ai` and the returned text is printed.

    Possible exceptions:
    - If `ask_ai` raises unexpected exceptions, catch and log them in
      `main.py` and show a generic error to the user (this is already done).
    """

    inputs = iter(["hello", "quit"])
    monkeypatch.setattr(builtins, "input", lambda prompt="": next(inputs))

    def fake_ask(q: str) -> str:
        return f"AI says: {q}"

    monkeypatch.setattr(main, "ask_ai", fake_ask)

    rc = main.main()
    assert rc == 0
    out = capsys.readouterr().out
    assert "AI says: hello" in out


def test_handle_query_ai_client_error(monkeypatch, capsys):
    """When `ask_ai` raises `AiClientError`, the CLI shows a friendly message.

    Possible exceptions and fixes:
    - If the error message leaks sensitive info (like API key), sanitize
      error messages before displaying them. Prefer logging full details.
    """

    inputs = iter(["ask", "quit"])
    monkeypatch.setattr(builtins, "input", lambda prompt="": next(inputs))

    def raise_client_error(q: str):
        raise AiClientError("provider failure")

    monkeypatch.setattr(main, "ask_ai", raise_client_error)

    rc = main.main()
    assert rc == 0
    out = capsys.readouterr().out
    assert "Error: provider failure" in out


def test_handle_query_unexpected_exception(monkeypatch, capsys):
    """When `ask_ai` raises an unexpected exception, the CLI shows a generic error.

    Recommended engineering response:
    - Log the full exception with a stack trace for debugging.
    - Return a generic message to the user to avoid exposing internals.
    """

    inputs = iter(["ask", "quit"])
    monkeypatch.setattr(builtins, "input", lambda prompt="": next(inputs))

    def raise_value_error(q: str):
        raise ValueError("bad payload")

    monkeypatch.setattr(main, "ask_ai", raise_value_error)

    rc = main.main()
    assert rc == 0
    out = capsys.readouterr().out
    assert "An unexpected error occurred" in out


def test_keyboard_interrupt_exits(monkeypatch, capsys):
    """Simulate Ctrl+C (KeyboardInterrupt) and verify clean exit.

    Engineering note:
    - KeyboardInterrupt should be treated as user intent to quit; the
      program should exit gracefully and not show a traceback.
    """

    def raise_kb(prompt=""):
        raise KeyboardInterrupt()

    monkeypatch.setattr(builtins, "input", raise_kb)

    rc = main.main()
    assert rc == 0
    out = capsys.readouterr().out
    assert "Goodbye!" in out
