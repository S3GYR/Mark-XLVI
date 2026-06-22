"""Secure wrapper for sending messages through desktop apps."""

from __future__ import annotations

from typing import Any

from jarvis.core.player import ConsolePlayer, Player
from jarvis.security.permissions import ActionContext

# Legacy implementations
from actions.send_message import (
    _send_discord,
    _send_instagram,
    _send_messenger,
    _send_signal,
    _send_telegram,
    _send_whatsapp,
)


SUPPORTED_PLATFORMS = {
    "whatsapp": _send_whatsapp,
    "telegram": _send_telegram,
    "signal": _send_signal,
    "discord": _send_discord,
    "instagram": _send_instagram,
    "messenger": _send_messenger,
}


def _safe_player(player: Any | None) -> Player:
    """Return a Player instance, using ConsolePlayer as fallback."""
    if player is None:
        return ConsolePlayer()
    return player


def send_message(
    parameters: dict | None = None,
    response: Any | None = None,
    player: Any | None = None,
    session_memory: Any | None = None,
) -> str:
    """Send a message via a desktop app after user confirmation."""
    params = parameters or {}
    platform = params.get("platform", "").lower().strip()
    receiver = params.get("receiver", "").strip()
    message = params.get("message", "").strip()
    p = _safe_player(player)

    if not platform:
        return "No platform specified."
    if not receiver:
        return "No receiver specified."
    if not message:
        return "No message provided."

    if platform not in SUPPORTED_PLATFORMS:
        return f"Unsupported platform: {platform}. Supported: {', '.join(SUPPORTED_PLATFORMS)}."

    ctx = ActionContext(
        "send_message",
        f"send message to {receiver} via {platform}: '{message[:80]}...'",
        p,
    )
    if not ctx.check():
        return "Action cancelled by user."

    p.write_log(f"[send_message] {platform} → {receiver}")

    try:
        sender = SUPPORTED_PLATFORMS[platform]
        return sender(receiver, message)
    except Exception as e:
        return f"Send message error: {e}"
