"""Tests for legacy tool wrappers validation paths."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from jarvis.tools import (
    code_helper,
    computer_control,
    desktop,
    dev_agent,
    open_app,
    send_message,
)


def patch_confirm():
    """Patch ActionContext.check to return False (cancelled)."""
    return patch("jarvis.security.permissions.ActionContext.check", return_value=False)


@pytest.mark.asyncio
async def test_desktop_missing_action():
    """desktop_control without action returns guidance."""
    result = await desktop.desktop_control({})
    assert "usage" in result.lower() or "action" in result.lower()


@pytest.mark.asyncio
async def test_desktop_wallpaper_no_path():
    """desktop_control wallpaper requires a path."""
    result = await desktop.desktop_control({"action": "wallpaper"})
    assert "No image path" in result


@pytest.mark.asyncio
async def test_desktop_wallpaper_url_no_url():
    """desktop_control wallpaper_url requires a URL."""
    result = await desktop.desktop_control({"action": "wallpaper_url"})
    assert "No URL" in result


def test_send_message_validation():
    """send_message validates required fields."""
    assert send_message.send_message({}) == "No platform specified."
    assert send_message.send_message({"platform": "whatsapp"}) == "No receiver specified."
    assert "No message" in send_message.send_message(
        {"platform": "whatsapp", "receiver": "alice"}
    )


def test_send_message_unsupported_platform():
    """send_message rejects unsupported platforms."""
    result = send_message.send_message(
        {"platform": "unknown", "receiver": "alice", "message": "hi"}
    )
    assert "Unsupported platform" in result


def test_computer_control_missing_action():
    """computer_control without action returns usage."""
    result = computer_control.computer_control({})
    assert "usage" in result.lower() or "action" in result.lower()


def test_computer_control_type_no_text():
    """computer_control type requires text."""
    result = computer_control.computer_control({"action": "type"})
    assert "No text" in result


def test_computer_control_click_no_coords():
    """computer_control click requires coordinates."""
    result = computer_control.computer_control({"action": "click"})
    assert "coordinates" in result.lower() or "x" in result.lower() or "y" in result.lower()


def test_computer_control_unknown_action():
    """computer_control reports unknown actions."""
    result = computer_control.computer_control({"action": "unknown_xyz"})
    assert "Unknown action" in result


def test_computer_control_user_profile():
    """computer_control user_profile returns a string."""
    result = computer_control.computer_control({"action": "user_profile"})
    assert isinstance(result, str)


def test_code_helper_no_description():
    """code_helper requires a description."""
    result = code_helper.code_helper({})
    assert "No description" in result or "No description, file path" in result


def test_code_helper_explain():
    """code_helper explain path returns a comment."""
    with patch("jarvis.tools.code_helper._get_llm_client") as mock_client, patch(
        "jarvis.security.permissions.ActionContext.check", return_value=True
    ):
        mock_client.return_value.chat.return_value.content = "This is a comment."
        result = code_helper.code_helper(
            {"description": "explain this", "language": "python", "action": "explain"}
        )
    assert "explain" in result.lower() or "comment" in result.lower() or "this is a comment" in result.lower()


def test_dev_agent_no_description():
    """dev_agent requires a description."""
    result = dev_agent.dev_agent({})
    assert "No project description" in result


def test_dev_agent_cancelled():
    """dev_agent cancelled by user."""
    with patch_confirm():
        result = dev_agent.dev_agent({"description": "test project"})
    assert "cancelled" in result.lower()


def test_open_app_alias():
    """open_app resolves aliases."""
    assert open_app._normalize("vscode") == "code"


def test_open_app_unknown():
    """open_app returns a message for unknown apps."""
    with patch("shutil.which", return_value=None):
        result = open_app.open_app({"app_name": "nonexistent_app_xyz"})
    assert "could not" in result.lower() or "not found" in result.lower() or "loading" in result.lower()


def test_open_app_blocked():
    """open_app rejects blocked applications."""
    result = open_app.open_app({"app_name": "cmd.exe"})
    assert "blocked" in result.lower()


def test_open_app_success():
    """open_app succeeds with a mocked launcher."""
    with patch("jarvis.tools.open_app._OS_LAUNCHERS", {"Windows": lambda x: True}):
        result = open_app.open_app({"app_name": "notepad"})
    assert "opened" in result.lower()
