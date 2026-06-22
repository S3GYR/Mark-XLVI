"""Tests for secrets management."""

from __future__ import annotations

from unittest.mock import patch

from jarvis.security.secrets import get_secret, set_secret


def test_get_secret_from_env():
    """Environment variable is read when available."""
    with patch.dict("os.environ", {"TEST_SECRET_KEY": "env-value"}, clear=False):
        value = get_secret("test_secret_key", env_override="TEST_SECRET_KEY")
        assert value == "env-value"


def test_get_secret_missing():
    """Missing secret returns None."""
    value = get_secret("nonexistent_secret_xyz", env_override="NONEXISTENT_SECRET_XYZ")
    assert value is None


def test_set_and_get_secret(tmp_path, monkeypatch):
    """Secret can be set and retrieved from fallback storage."""
    from jarvis.config.paths import CONFIG_DIR
    monkeypatch.setattr("jarvis.config.paths.CONFIG_DIR", tmp_path)
    set_secret("test-key", "test-value")
    assert get_secret("test-key") == "test-value"
