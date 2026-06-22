"""Tests for dashboard auth manager."""

from __future__ import annotations

import time

import pytest

from jarvis.config.settings import Settings
from jarvis.web.auth import AuthManager


@pytest.fixture
def auth() -> AuthManager:
    return AuthManager(Settings())


def test_new_pin(auth: AuthManager):
    """PINs are generated and can be validated."""
    pin = auth.new_pin()
    assert len(pin) == 6
    assert pin.isdigit()


def test_validate_pin_success(auth: AuthManager):
    """A valid PIN returns a session key."""
    pin = auth.new_pin()
    key = auth.validate_pin(pin, "127.0.0.1")
    assert key is not None
    assert len(key) == 32


def test_validate_pin_failure(auth: AuthManager):
    """An invalid PIN returns None."""
    result = auth.validate_pin("000000", "127.0.0.1")
    assert result is None


def test_rate_limit_lockout(auth: AuthManager):
    """Repeated failures lock out the IP."""
    # Ensure the tested PIN is not accidentally a pending PIN.
    auth._pending_pins.clear()
    ip = "192.0.2.1"
    for _ in range(5):
        auth.validate_pin("000000", ip)
    assert auth.is_locked_out(ip)


def test_token_lifecycle(auth: AuthManager):
    """Tokens can be created and validated."""
    session_key = "test-key"
    token = auth.create_token(session_key)
    assert auth.is_valid_token(token)
    assert auth.get_aes_key(token) is not None


def test_revoke_devices(auth: AuthManager):
    """Device sessions can be revoked."""
    dev = auth.create_device_session("key")
    assert auth.validate_device_token(dev) == "key"
    assert auth.revoke_devices() == 1
    assert auth.validate_device_token(dev) is None
