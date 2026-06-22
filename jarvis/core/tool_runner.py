"""Tool execution bridge: secure wrappers + legacy actions."""

from __future__ import annotations

import asyncio
import traceback
from typing import Any

from jarvis.core.player import Player
from jarvis.observability.logger import get_logger
from jarvis.observability.tracing import instrument_async
from jarvis.tools.registry import get_tool_function

logger = get_logger(__name__)

# Legacy action imports (kept for actions not yet wrapped)
from actions.computer_settings import computer_settings
from actions.file_controller import file_controller
from actions.file_processor import file_processor
from actions.flight_finder import flight_finder
from actions.game_updater import game_updater
from actions.reminder import reminder
from actions.screen_processor import screen_process
from actions.weather_report import weather_action
from actions.web_search import web_search as web_search_action
from actions.youtube_video import youtube_video


# Legacy actions that are not yet wrapped securely
_LEGACY_ACTIONS: dict[str, Any] = {
    "weather_report": weather_action,
    "file_controller": file_controller,
    "reminder": reminder,
    "youtube_video": youtube_video,
    "screen_process": screen_process,
    "computer_settings": computer_settings,
    "web_search": web_search_action,
    "file_processor": file_processor,
    "game_updater": game_updater,
    "flight_finder": flight_finder,
}


class ToolRunner:
    """Execute a tool call using the secure registry when available.

    Falls back to legacy actions for tools that have not been wrapped yet.
    """

    def __init__(self, player: Player):
        self.player = player

    @instrument_async("tool_runner.run")
    async def run(self, name: str, args: dict[str, Any]) -> str:
        """Execute a tool by name and return its result."""
        logger.info("tool_called", tool=name, args=args)
        self.player.write_log(f"[tool] {name}")

        try:
            # Prefer secure wrapper
            func = get_tool_function(name)
            if func is not None:
                result = await self._call(func, args)
                return str(result) if result is not None else "Done."

            # Fallback to legacy action
            legacy = _LEGACY_ACTIONS.get(name)
            if legacy is not None:
                result = await self._call_legacy(legacy, args)
                return str(result) if result is not None else "Done."

            return f"Unknown tool: {name}"

        except Exception as e:
            logger.error("tool_failed", tool=name, error=str(e))
            traceback.print_exc()
            return f"Tool '{name}' failed: {e}"

    async def _call(self, func: Any, args: dict[str, Any]) -> Any:
        """Call a secure wrapper function (sync or async)."""
        if asyncio.iscoroutinefunction(func):
            return await func(args, player=self.player)
        return await asyncio.get_event_loop().run_in_executor(
            None, lambda: func(args, player=self.player)
        )

    async def _call_legacy(self, func: Any, args: dict[str, Any]) -> Any:
        """Call a legacy action function."""
        kwargs = {"parameters": args, "player": self.player, "response": None}
        if asyncio.iscoroutinefunction(func):
            return await func(**kwargs)
        return await asyncio.get_event_loop().run_in_executor(None, lambda: func(**kwargs))

    async def handle_memory_save(self, args: dict[str, Any]) -> dict[str, Any]:
        """Handle the save_memory tool inline."""
        category = args.get("category", "notes")
        key = args.get("key", "")
        value = args.get("value", "")
        if key and value:
            logger.info("memory_save", category=category, key=key)
        return {"result": "ok", "silent": True}
