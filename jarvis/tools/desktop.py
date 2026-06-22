"""Secure wrapper for desktop automation actions."""

from __future__ import annotations

from typing import Any

from jarvis.core.player import ConsolePlayer, Player
from jarvis.security.permissions import ActionContext
from jarvis.security.sandbox import SandboxError, execute_code

# Import legacy action implementations
from actions.desktop import (
    clean_desktop,
    get_current_wallpaper,
    get_desktop_stats,
    list_desktop,
    organize_desktop,
    set_wallpaper,
    set_wallpaper_from_url,
)


def _safe_player(player: Any | None) -> Player:
    """Return a Player instance, using ConsolePlayer as fallback."""
    if player is None:
        return ConsolePlayer()
    return player


async def desktop_control(
    parameters: dict | None = None,
    response: Any | None = None,
    player: Any | None = None,
    session_memory: Any | None = None,
) -> str:
    """Execute a desktop action with user confirmation and sandboxing."""
    params = parameters or {}
    action = params.get("action", "").lower().strip()
    task = params.get("task", "").strip()
    actual_task = task or params.get("description", "")
    p = _safe_player(player)

    p.write_log(f"[desktop] {action or actual_task[:40]}")

    try:
        if action == "wallpaper":
            path = params.get("path", "")
            if not path:
                return "No image path provided."
            ctx = ActionContext("desktop_control", f"set wallpaper to {path}", p)
            if not ctx.check():
                return "Action cancelled by user."
            return set_wallpaper(path)

        elif action == "wallpaper_url":
            url = params.get("url", "")
            if not url:
                return "No URL provided."
            ctx = ActionContext("desktop_control", f"set wallpaper from URL {url}", p)
            if not ctx.check():
                return "Action cancelled by user."
            return set_wallpaper_from_url(url)

        elif action == "current_wallpaper":
            return get_current_wallpaper()

        elif action == "organize":
            mode = params.get("mode", "by_type")
            ctx = ActionContext("desktop_control", f"organize desktop ({mode})", p)
            if not ctx.check():
                return "Action cancelled by user."
            return organize_desktop(mode)

        elif action == "clean":
            ctx = ActionContext("desktop_control", "clean desktop into archive", p)
            if not ctx.check():
                return "Action cancelled by user."
            return clean_desktop()

        elif action == "list":
            return list_desktop()

        elif action == "stats":
            return get_desktop_stats()

        elif action == "task" or actual_task:
            ctx = ActionContext("desktop_control", f"AI-powered desktop task: {actual_task}", p)
            if not ctx.check():
                return "Action cancelled by user."
            return await _execute_ai_task(actual_task, p)

        else:
            return "No action or task specified."

    except Exception as e:
        return f"Desktop control error: {e}"


async def _execute_ai_task(task: str, player: Player) -> str:
    """Execute an AI-generated desktop task inside the sandbox.

    This replaces the legacy exec() call with a subprocess-based sandbox.
    """
    from jarvis.llm.client import LLMClient, ToolDeclaration

    player.write_log("[Desktop] Generating safe action plan...")

    client = LLMClient()
    prompt = f"""You are a desktop automation assistant.

Generate safe Python code to accomplish this task: {task}

Allowed:
- pathlib.Path (read-only, no deletion)
- math, random, datetime, time, json, re, statistics
- No imports, no network, no subprocess, no file deletion, no eval/exec.

Output ONLY the Python code. If unsafe, output: UNSAFE"""

    try:
        resp = client.chat(
            messages=[{"role": "user", "content": prompt}],
            model="gemini/gemini-2.5-flash",
        )
        code = resp.content or "UNSAFE"
    except Exception as e:
        return f"Could not generate action plan: {e}"

    try:
        result = execute_code(code)
        if result["success"]:
            return result["stdout"] or "Done."
        return f"Execution error: {result['stderr']}"
    except SandboxError as e:
        return str(e)
