"""Tests for the secure browser_control wrapper."""

from __future__ import annotations

from jarvis.tools.browser_control import _is_url_forbidden


def test_localhost_forbidden():
    assert _is_url_forbidden("http://localhost:3000")


def test_127_forbidden():
    assert _is_url_forbidden("http://127.0.0.1/admin")


def test_private_ip_forbidden():
    assert _is_url_forbidden("http://192.168.1.1")
    assert _is_url_forbidden("http://10.0.0.1")


def test_public_url_allowed():
    assert not _is_url_forbidden("https://google.com")
    assert not _is_url_forbidden("https://github.com/search")
