"""Tests for the permission framework."""

from __future__ import annotations

from jarvis.core.player import ConsolePlayer
from jarvis.security.permissions import (
    RiskLevel,
    confirm_action,
    get_tool_risk_level,
    is_confirmation_required,
)


def test_get_tool_risk_level():
    """Risk levels are assigned to tools."""
    assert get_tool_risk_level("open_app") == RiskLevel.LOW
    assert get_tool_risk_level("dev_agent") == RiskLevel.CRITICAL


def test_is_confirmation_required_high_risk(monkeypatch):
    """High-risk tools require confirmation when enabled."""
    from jarvis.config.settings import get_settings

    monkeypatch.setattr(get_settings(), "require_confirmation", True)
    assert is_confirmation_required("desktop_control") is True


def test_is_confirmation_required_low_risk(monkeypatch):
    """Low-risk tools do not require confirmation."""
    from jarvis.config.settings import get_settings

    monkeypatch.setattr(get_settings(), "require_confirmation", True)
    assert is_confirmation_required("open_app") is False


def test_confirm_action_without_player(monkeypatch):
    """High-risk actions without a player are denied."""
    from jarvis.config.settings import get_settings

    monkeypatch.setattr(get_settings(), "require_confirmation", True)
    assert confirm_action("dev_agent", "deploy code") is False


def test_confirm_action_with_player(monkeypatch):
    """High-risk actions can be approved by a player."""
    from jarvis.config.settings import get_settings

    monkeypatch.setattr(get_settings(), "require_confirmation", True)
    player = ConsolePlayer()
    player.request_confirmation = lambda _: True
    assert confirm_action("dev_agent", "deploy code", player) is True
