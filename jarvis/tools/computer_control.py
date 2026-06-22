"""Secure wrapper for computer control (keyboard, mouse, screenshots)."""

from __future__ import annotations

from typing import Any

from jarvis.core.player import ConsolePlayer, Player
from jarvis.security.permissions import ActionContext

# Legacy low-level functions
from actions.computer_control import (
    _click,
    _hotkey,
    _press,
    _random_data,
    _scroll,
    _smart_type,
    _type,
    _user_profile,
)


def _safe_player(player: Any | None) -> Player:
    """Return a Player instance, using ConsolePlayer as fallback."""
    if player is None:
        return ConsolePlayer()
    return player


def computer_control(
    parameters: dict | None = None,
    response: Any | None = None,
    player: Any | None = None,
    session_memory: Any | None = None,
) -> str:
    """Execute computer control actions with user confirmation.

    This is a high-risk tool that simulates keyboard/mouse input. Every action
    requires explicit user confirmation.
    """
    params = parameters or {}
    action = params.get("action", "").lower().strip()
    p = _safe_player(player)

    text = params.get("text", "")
    x = params.get("x")
    y = params.get("y")
    key = params.get("key", "")
    keys = params.get("keys", [])
    direction = params.get("direction", "down")
    amount = params.get("amount", 3)
    data_type = params.get("data_type", "")
    interval = params.get("interval", 0.03)

    p.write_log(f"[computer_control] {action}")

    try:
        if action == "type":
            if not text:
                return "No text provided."
            ctx = ActionContext("computer_control", f"type '{text[:60]}...'", p)
            if not ctx.check():
                return "Action cancelled by user."
            return _type(text, interval)

        elif action == "smart_type":
            if not text:
                return "No text provided."
            ctx = ActionContext("computer_control", f"smart-type '{text[:60]}...'", p)
            if not ctx.check():
                return "Action cancelled by user."
            return _smart_type(text, clear_first=params.get("clear_first", True))

        elif action == "click":
            ctx = ActionContext("computer_control", f"click at ({x}, {y})", p)
            if not ctx.check():
                return "Action cancelled by user."
            return _click(x, y, button=params.get("button", "left"), clicks=params.get("clicks", 1))

        elif action == "hotkey":
            if not keys:
                return "No keys provided."
            ctx = ActionContext("computer_control", f"hotkey {'+'.join(keys)}", p)
            if not ctx.check():
                return "Action cancelled by user."
            return _hotkey(*keys)

        elif action == "press":
            if not key:
                return "No key provided."
            ctx = ActionContext("computer_control", f"press key '{key}'", p)
            if not ctx.check():
                return "Action cancelled by user."
            return _press(key)

        elif action == "scroll":
            ctx = ActionContext("computer_control", f"scroll {direction} {amount}", p)
            if not ctx.check():
                return "Action cancelled by user."
            return _scroll(direction, amount)

        elif action == "random_data":
            if not data_type:
                return "No data_type provided."
            return _random_data(data_type)

        elif action == "user_profile":
            return str(_user_profile())

        else:
            return f"Unknown action: {action}"

    except Exception as e:
        return f"Computer control error: {e}"
