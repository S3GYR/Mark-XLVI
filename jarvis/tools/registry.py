"""Tool registry and declarations for the LLM."""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from jarvis.tools import code_helper as code_helper_tool
from jarvis.tools import computer_control as computer_control_tool
from jarvis.tools import desktop as desktop_tool
from jarvis.tools import dev_agent as dev_agent_tool
from jarvis.tools import open_app as open_app_tool
from jarvis.tools import send_message as send_message_tool

# Optional browser control wrapper (requires Playwright)
try:
    from jarvis.tools import browser_control as browser_control_tool
except Exception:
    browser_control_tool = None  # type: ignore[assignment]

# Map legacy tool names to secure wrapper implementations.
# This registry will be extended as each legacy action is wrapped.
_TOOL_FUNCTIONS: dict[str, Callable[..., str | Awaitable[str]]] = {
    "open_app": open_app_tool.open_app,
    "desktop_control": desktop_tool.desktop_control,
    "computer_control": computer_control_tool.computer_control,
    "send_message": send_message_tool.send_message,
    "code_helper": code_helper_tool.code_helper,
    "dev_agent": dev_agent_tool.dev_agent,
}
if browser_control_tool is not None:
    _TOOL_FUNCTIONS["browser_control"] = browser_control_tool.browser_control


# LiteLLM-compatible tool declarations.
_TOOL_DECLARATIONS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "open_app",
            "description": (
                "Opens a known application on the computer. "
                "Use this whenever the user asks to open, launch, or start an app, "
                "website, or program."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {
                        "type": "string",
                        "description": "Exact name of the application (e.g. 'Chrome', 'Spotify', 'VSCode')",
                    },
                },
                "required": ["app_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "desktop_control",
            "description": (
                "Performs desktop organization, wallpaper, or listing tasks. "
                "For AI-generated automation tasks, the action is sandboxed."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": (
                            "One of: wallpaper, wallpaper_url, current_wallpaper, "
                            "organize, clean, list, stats, task"
                        ),
                    },
                    "path": {"type": "string", "description": "Image path for wallpaper action"},
                    "url": {"type": "string", "description": "Image URL for wallpaper_url action"},
                    "mode": {
                        "type": "string",
                        "description": "by_type or by_date for organize action",
                    },
                    "task": {
                        "type": "string",
                        "description": "Natural language description for AI-powered tasks",
                    },
                },
                "required": ["action"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "computer_control",
            "description": "Simulates keyboard and mouse input. Requires user confirmation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "One of: type, smart_type, click, hotkey, press, scroll, random_data, user_profile",
                    },
                    "text": {"type": "string", "description": "Text to type"},
                    "x": {"type": "number", "description": "X coordinate for click"},
                    "y": {"type": "number", "description": "Y coordinate for click"},
                    "key": {"type": "string", "description": "Key to press"},
                    "keys": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Keys for hotkey combination",
                    },
                    "direction": {"type": "string", "description": "Scroll direction"},
                    "amount": {"type": "number", "description": "Scroll amount"},
                    "data_type": {"type": "string", "description": "Type of random data to generate"},
                    "interval": {"type": "number", "description": "Typing interval"},
                    "clear_first": {"type": "boolean", "description": "Clear field before typing"},
                },
                "required": ["action"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "send_message",
            "description": "Send a message via a desktop messaging app. Requires user confirmation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "platform": {
                        "type": "string",
                        "description": "whatsapp, telegram, signal, discord, instagram, messenger",
                    },
                    "receiver": {"type": "string", "description": "Contact name or username"},
                    "message": {"type": "string", "description": "Message text"},
                },
                "required": ["platform", "receiver", "message"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "code_helper",
            "description": "Generate, fix, explain, or run code. Execution is sandboxed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "description": {"type": "string", "description": "What to do with the code"},
                    "language": {"type": "string", "description": "Programming language"},
                    "output_path": {"type": "string", "description": "Path to save generated code"},
                    "file_path": {"type": "string", "description": "Path to existing file"},
                    "code": {"type": "string", "description": "Code snippet"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "dev_agent",
            "description": "Create or fix a multi-file project. Requires user confirmation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "description": {"type": "string", "description": "Project description"},
                    "language": {"type": "string", "description": "Programming language"},
                    "fix_mode": {"type": "boolean", "description": "Whether to fix an existing project"},
                    "project_dir": {"type": "string", "description": "Project directory for fix mode"},
                    "error_output": {"type": "string", "description": "Error output for fix mode"},
                },
                "required": ["description"],
            },
        },
    },
]

if browser_control_tool is not None:
    _TOOL_DECLARATIONS.append({
        "type": "function",
        "function": {
            "name": "browser_control",
            "description": "Control a browser via Playwright. SSRF protection enabled.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "One of: go_to, search, click, type, fill_form, smart_click, smart_type, get_text, get_url, press, new_tab, close_tab, screenshot, back, forward, reload, close, switch, list_browsers, close_all",
                    },
                    "url": {"type": "string", "description": "URL to navigate to"},
                    "query": {"type": "string", "description": "Search query"},
                    "selector": {"type": "string", "description": "CSS selector"},
                    "text": {"type": "string", "description": "Text to type"},
                    "engine": {"type": "string", "description": "Search engine"},
                    "fields": {"type": "object", "description": "Form fields"},
                    "description": {"type": "string", "description": "Description for smart click/type"},
                    "direction": {"type": "string", "description": "Scroll direction"},
                    "amount": {"type": "number", "description": "Scroll amount"},
                    "key": {"type": "string", "description": "Key to press"},
                    "path": {"type": "string", "description": "Screenshot path"},
                    "browser": {"type": "string", "description": "Browser name"},
                    "target": {"type": "string", "description": "Browser target for switch"},
                    "clear_first": {"type": "boolean", "description": "Clear before typing"},
                },
                "required": ["action"],
            },
        },
    })


def get_tool_declaration(name: str) -> dict[str, Any] | None:
    """Return the LiteLLM declaration for a tool."""
    for decl in _TOOL_DECLARATIONS:
        if decl["function"]["name"] == name:
            return decl
    return None


def get_tool_function(name: str) -> Callable[..., str | Awaitable[str]] | None:
    """Return the implementation for a tool."""
    return _TOOL_FUNCTIONS.get(name)


def list_tools() -> list[str]:
    """Return all registered tool names."""
    return list(_TOOL_FUNCTIONS.keys())


def get_tool_declarations() -> list[dict[str, Any]]:
    """Return all tool declarations."""
    return list(_TOOL_DECLARATIONS)


def register_tool(
    name: str,
    func: Callable[..., str | Awaitable[str]],
    declaration: dict[str, Any],
) -> None:
    """Register a new tool at runtime."""
    _TOOL_FUNCTIONS[name] = func
    _TOOL_DECLARATIONS.append(declaration)
