"""Secure wrapper for browser automation via Playwright."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

from jarvis.core.player import ConsolePlayer, Player
from jarvis.security.permissions import ActionContext

# Import legacy registry and session (optional if Playwright is unavailable)
try:
    from actions.browser_control import _registry as _legacy_registry
    from actions.browser_control import browser_control as _legacy_browser_control
except Exception:
    _legacy_registry = None  # type: ignore[assignment]
    _legacy_browser_control = None  # type: ignore[assignment]

# Actions that can change state or navigate
_HIGH_RISK_ACTIONS = {
    "go_to",
    "click",
    "type",
    "fill_form",
    "smart_click",
    "smart_type",
    "new_tab",
    "close_tab",
    "close",
    "close_all",
}

# URLs that are forbidden to prevent SSRF / local network attacks
_FORBIDDEN_HOSTS = {
    "localhost",
    "127.0.0.1",
    "::1",
    "0.0.0.0",
    "169.254.",
    "10.",
    "192.168.",
    "172.16.",
    "172.17.",
    "172.18.",
    "172.19.",
    "172.20.",
    "172.21.",
    "172.22.",
    "172.23.",
    "172.24.",
    "172.25.",
    "172.26.",
    "172.27.",
    "172.28.",
    "172.29.",
    "172.30.",
    "172.31.",
}



def _safe_player(player: Any | None) -> Player:
    """Return a Player instance, using ConsolePlayer as fallback."""
    if player is None:
        return ConsolePlayer()
    return player


def _is_url_forbidden(url: str) -> bool:
    """Return True if the URL points to a forbidden local/internal host."""
    if not url:
        return False
    try:
        parsed = urlparse(url if "://" in url else f"https://{url}")
        host = parsed.hostname or ""
        host_lower = host.lower()
        for forbidden in _FORBIDDEN_HOSTS:
            if host_lower == forbidden or host_lower.startswith(forbidden):
                return True
        # Block bare IP addresses (simple heuristic)
        if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", host):
            return True
    except Exception:
        pass
    return False


def _sanitize_parameters(params: dict) -> tuple[dict, list[str]]:
    """Sanitize browser parameters and return (params, blocked_reasons)."""
    reasons: list[str] = []
    sanitized = dict(params)

    url = sanitized.get("url", "")
    if _is_url_forbidden(url):
        reasons.append(f"URL '{url}' points to a local/internal host")
        sanitized["url"] = "about:blank"

    query = sanitized.get("query", "")
    if _is_url_forbidden(query):
        reasons.append(f"Search query contains forbidden URL")
        sanitized["query"] = ""

    return sanitized, reasons


def browser_control(
    parameters: dict | None = None,
    response: Any | None = None,
    player: Any | None = None,
    session_memory: Any | None = None,
) -> str:
    """Execute a browser action with SSRF protection and confirmation."""
    params = parameters or {}
    action = params.get("action", "").lower().strip()
    p = _safe_player(player)

    sanitized, reasons = _sanitize_parameters(params)
    if reasons:
        p.write_log(f"[browser_control] blocked: {', '.join(reasons)}")
        return f"Blocked for security: {', '.join(reasons)}"

    p.write_log(f"[browser_control] {action}")

    if action in _HIGH_RISK_ACTIONS:
        ctx = ActionContext("browser_control", f"{action} in browser", p)
        if not ctx.check():
            return "Action cancelled by user."

    if _legacy_browser_control is None:
        return "Browser control unavailable (Playwright not installed)."

    try:
        return _legacy_browser_control(sanitized, response, player, session_memory)
    except Exception as e:
        return f"Browser control error: {e}"


def close_all_browsers() -> str:
    """Close all active browser sessions."""
    if _legacy_registry is None:
        return "Browser control unavailable (Playwright not installed)."
    try:
        return _legacy_registry.close_all()
    except Exception as e:
        return f"Could not close browsers: {e}"
