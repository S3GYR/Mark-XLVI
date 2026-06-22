"""UI constants, colors, and styling."""

from __future__ import annotations

from pathlib import Path
import platform
import sys


def _base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent.parent


BASE_DIR = _base_dir()
CONFIG_DIR = BASE_DIR / "config"
API_FILE = CONFIG_DIR / "api_keys.json"

DEFAULT_W, DEFAULT_H = 980, 700
MIN_W, MIN_H = 820, 580
LEFT_W = 148
RIGHT_W = 340

OS = platform.system()


class Colors:
    BG = "#00060a"
    PANEL = "#010d14"
    PANEL2 = "#010f18"
    BORDER = "#0d3347"
    BORDER_B = "#1a5c7a"
    BORDER_A = "#0f4060"
    PRI = "#00d4ff"
    PRI_DIM = "#007a99"
    PRI_GHO = "#001f2e"
    ACC = "#ff6b00"
    ACC2 = "#ffcc00"
    GREEN = "#00ff88"
    GREEN_D = "#00aa55"
    RED = "#ff3355"
    MUTED = "#ff3366"
    TEXT = "#8ffcff"
    TEXT_DIM = "#3a8a9a"
    TEXT_MED = "#5ab8cc"
    WHITE = "#d8f8ff"
    DARK = "#000d14"
    BAR_BG = "#011520"


C = Colors


def qcol(h: str, a: int = 255):
    """Return a QColor with optional alpha."""
    from PyQt6.QtGui import QColor
    c = QColor(h)
    c.setAlpha(a)
    return c
