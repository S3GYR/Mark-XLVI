"""Tests for UI constants."""

from __future__ import annotations

from jarvis.ui.constants import BASE_DIR, Colors, qcol


def test_colors_are_hex():
    """All colors are non-empty strings."""
    c = Colors
    assert c.BG.startswith("#")
    assert c.PRI.startswith("#")


def test_qcol_returns_qcolor():
    """qcol returns a QColor with expected alpha."""
    col = qcol("#ff0000", 128)
    assert col.alpha() == 128
    assert col.red() == 255


def test_base_dir_exists():
    """Base directory points to the project root."""
    assert (BASE_DIR / "pyproject.toml").exists()
