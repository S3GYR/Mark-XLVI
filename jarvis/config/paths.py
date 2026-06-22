"""Centralized path management for JARVIS."""

from __future__ import annotations

import sys
from pathlib import Path

import platformdirs


def get_base_dir() -> Path:
    """Return the project root directory."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent.parent


def get_data_dir() -> Path:
    """Return user data directory outside the source tree."""
    return Path(platformdirs.user_data_dir("jarvis", "mark-xlvi"))


def get_config_dir() -> Path:
    """Return user config directory outside the source tree."""
    return Path(platformdirs.user_config_dir("jarvis", "mark-xlvi"))


def get_cache_dir() -> Path:
    """Return user cache directory."""
    return Path(platformdirs.user_cache_dir("jarvis", "mark-xlvi"))


BASE_DIR = get_base_dir()
DATA_DIR = get_data_dir()
CONFIG_DIR = get_config_dir()
CACHE_DIR = get_cache_dir()

PROMPT_PATH = BASE_DIR / "core" / "prompt.txt"

# Legacy paths for migration
LEGACY_CONFIG_DIR = BASE_DIR / "config"
LEGACY_CONFIG_FILE = LEGACY_CONFIG_DIR / "api_keys.json"
LEGACY_MEMORY_FILE = BASE_DIR / "memory" / "long_term.json"
