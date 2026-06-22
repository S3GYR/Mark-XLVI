"""Player protocol used by tools to interact with the UI or logs."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class Player(Protocol):
    """Minimal interface that tools can use without depending on PyQt6."""

    def write_log(self, text: str) -> None:
        """Write a log message to the user interface."""
        ...

    def set_state(self, state: str) -> None:
        """Update the assistant state shown in the UI."""
        ...

    def request_confirmation(self, message: str) -> bool:
        """Request explicit user confirmation for an action.

        Returns True if the user confirms.
        """
        ...

    @property
    def muted(self) -> bool:
        """Return True if the assistant is muted."""
        ...

    @property
    def current_file(self) -> str | None:
        """Return the currently dropped file path, if any."""
        ...

    def speak(self, text: str) -> None:
        """Speak text through the TTS engine."""
        ...


class ConsolePlayer:
    """Fallback Player that writes to the console."""

    def __init__(self) -> None:
        self._muted = False
        self._current_file: str | None = None

    def write_log(self, text: str) -> None:
        print(text)

    def set_state(self, state: str) -> None:
        print(f"[state] {state}")

    def request_confirmation(self, message: str) -> bool:
        response = input(f"{message} (y/N): ").strip().lower()
        return response in {"y", "yes"}

    @property
    def muted(self) -> bool:
        return self._muted

    @property
    def current_file(self) -> str | None:
        return self._current_file

    def speak(self, text: str) -> None:
        if not self._muted:
            print(f"[TTS] {text}")
