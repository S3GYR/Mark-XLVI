"""Permission and confirmation framework for dangerous actions."""

from __future__ import annotations

from enum import Enum
from typing import Protocol

from jarvis.config.settings import get_settings


class RiskLevel(str, Enum):
    """Risk level for a tool invocation."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Player(Protocol):
    """Minimal interface for UI-driven confirmations."""

    def request_confirmation(self, message: str) -> bool:
        """Return True if the user confirms the action."""
        ...


# Mapping of tool names to their default risk level
TOOL_RISK_LEVELS: dict[str, RiskLevel] = {
    "open_app": RiskLevel.LOW,
    "web_search": RiskLevel.LOW,
    "weather_action": RiskLevel.LOW,
    "reminder": RiskLevel.LOW,
    "youtube_video": RiskLevel.LOW,
    "computer_settings": RiskLevel.MEDIUM,
    "send_message": RiskLevel.HIGH,
    "file_controller": RiskLevel.HIGH,
    "desktop_control": RiskLevel.HIGH,
    "code_helper": RiskLevel.HIGH,
    "dev_agent": RiskLevel.CRITICAL,
    "browser_control": RiskLevel.HIGH,
    "computer_control": RiskLevel.HIGH,
    "screen_process": RiskLevel.MEDIUM,
    "game_updater": RiskLevel.MEDIUM,
    "flight_finder": RiskLevel.LOW,
    "file_processor": RiskLevel.HIGH,
}


def get_tool_risk_level(tool_name: str) -> RiskLevel:
    """Return the risk level for a given tool."""
    return TOOL_RISK_LEVELS.get(tool_name, RiskLevel.MEDIUM)


def is_confirmation_required(tool_name: str, risk_level: RiskLevel | None = None) -> bool:
    """Return whether the tool requires explicit user confirmation."""
    settings = get_settings()
    if not settings.require_confirmation:
        return False

    level = risk_level or get_tool_risk_level(tool_name)
    return level in {RiskLevel.HIGH, RiskLevel.CRITICAL}


def confirm_action(tool_name: str, description: str, player: Player | None = None) -> bool:
    """Request user confirmation for a high-risk action.

    If no player is available, defaults to denying the action.
    """
    if not is_confirmation_required(tool_name):
        return True

    if player is None:
        return False

    message = f"{tool_name} wants to: {description}\nConfirm?"
    return player.request_confirmation(message)


class ActionContext:
    """Context for an action that may require approval."""

    def __init__(self, tool_name: str, description: str, player: Player | None = None):
        self.tool_name = tool_name
        self.description = description
        self.player = player
        self.risk_level = get_tool_risk_level(tool_name)
        self.approved = False

    def check(self) -> bool:
        """Return True if the action is allowed to proceed."""
        self.approved = confirm_action(self.tool_name, self.description, self.player)
        return self.approved
