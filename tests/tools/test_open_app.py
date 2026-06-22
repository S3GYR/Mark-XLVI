"""Tests for the secure open_app wrapper."""

from __future__ import annotations

import pytest

from jarvis.tools.open_app import _is_blocked, _normalize


def test_is_blocked_terminal():
    """Terminal applications are blocked."""
    assert _is_blocked("cmd.exe")
    assert _is_blocked("powershell")
    assert _is_blocked("bash")


def test_is_blocked_command_injection():
    """Strings with shell metacharacters are blocked."""
    assert _is_blocked("chrome; rm -rf /")
    assert _is_blocked("notepad && whoami")


def test_is_blocked_safe_app():
    """Normal apps are allowed."""
    assert not _is_blocked("chrome")
    assert not _is_blocked("spotify")


def test_normalize_alias():
    """Aliases are normalized to OS-specific names."""
    assert _normalize("google chrome") == "chrome"
    assert _normalize("vscode") == "code"


def test_open_app_blocked(monkeypatch):
    """Opening a blocked app is rejected."""
    from jarvis.tools import open_app

    monkeypatch.setattr(open_app, "_is_blocked", lambda _: True)
    result = open_app.open_app({"app_name": "cmd.exe"})
    assert "blocked" in result.lower()
