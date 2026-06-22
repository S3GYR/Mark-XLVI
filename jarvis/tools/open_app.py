"""Secure wrapper for opening applications."""

from __future__ import annotations

import platform
import shutil
import subprocess
import time
from typing import Any

_SYSTEM = platform.system()

# Blocked dangerous applications/commands
BLOCKED_APP_PATTERNS = {
    "cmd.exe",
    "powershell.exe",
    "powershell_ise.exe",
    "bash",
    "sh",
    "zsh",
    " Terminal",
    "wt",  # Windows Terminal
    "sudo",
    "su",
    "rm",
    "del",
    "format",
    "diskpart",
    "regedit",
    "taskkill",
    "netsh",
    "iptables",
    "ufw",
    "firewalld",
}

_APP_ALIASES: dict[str, dict[str, str]] = {
    "chrome": {"Windows": "chrome", "Darwin": "Google Chrome", "Linux": "google-chrome"},
    "google chrome": {"Windows": "chrome", "Darwin": "Google Chrome", "Linux": "google-chrome"},
    "firefox": {"Windows": "firefox", "Darwin": "Firefox", "Linux": "firefox"},
    "edge": {"Windows": "msedge", "Darwin": "Microsoft Edge", "Linux": "microsoft-edge"},
    "safari": {"Windows": "msedge", "Darwin": "Safari", "Linux": "firefox"},
    "vscode": {"Windows": "code", "Darwin": "Visual Studio Code", "Linux": "code"},
    "visual studio code": {"Windows": "code", "Darwin": "Visual Studio Code", "Linux": "code"},
    "code": {"Windows": "code", "Darwin": "Visual Studio Code", "Linux": "code"},
    "spotify": {"Windows": "Spotify", "Darwin": "Spotify", "Linux": "spotify"},
    "vlc": {"Windows": "vlc", "Darwin": "VLC", "Linux": "vlc"},
    "notepad": {"Windows": "notepad.exe", "Darwin": "TextEdit", "Linux": "gedit"},
    "explorer": {"Windows": "explorer.exe", "Darwin": "Finder", "Linux": "nautilus"},
    "file explorer": {"Windows": "explorer.exe", "Darwin": "Finder", "Linux": "nautilus"},
    "calculator": {"Windows": "calc.exe", "Darwin": "Calculator", "Linux": "gnome-calculator"},
    "settings": {"Windows": "ms-settings:", "Darwin": "System Preferences", "Linux": "gnome-control-center"},
}


def _is_blocked(app_name: str) -> bool:
    """Return True if the app name is blocked for security reasons."""
    normalized = app_name.lower().strip()
    for pattern in BLOCKED_APP_PATTERNS:
        if pattern in normalized or normalized == pattern:
            return True
    # Reject command separators and path traversal
    if any(c in app_name for c in ";|&$><`\n\r"):
        return True
    return False


def _normalize(raw: str) -> str:
    """Normalize an application name using the alias map."""
    key = raw.lower().strip()
    if key in _APP_ALIASES:
        return _APP_ALIASES[key].get(_SYSTEM, raw)
    for alias_key, os_map in _APP_ALIASES.items():
        if alias_key in key or key in alias_key:
            return os_map.get(_SYSTEM, raw)
    return raw


def _launch_windows(app_name: str) -> bool:
    """Launch an application on Windows without shell=True."""
    if shutil.which(app_name) or shutil.which(app_name.split(".")[0]):
        try:
            subprocess.Popen(
                [app_name],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            time.sleep(1.5)
            return True
        except Exception as e:
            print(f"[open_app] subprocess failed: {e}")

    if ":" in app_name:
        try:
            subprocess.Popen(
                ["start", app_name],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                shell=False,
            )
            time.sleep(1.0)
            return True
        except Exception:
            pass

    return False


def _launch_macos(app_name: str) -> bool:
    """Launch an application on macOS without shell=True."""
    try:
        result = subprocess.run(
            ["open", "-a", app_name],
            capture_output=True,
            timeout=8,
            shell=False,
        )
        if result.returncode == 0:
            time.sleep(1.0)
            return True
    except Exception:
        pass

    try:
        result = subprocess.run(
            ["open", "-a", f"{app_name}.app"],
            capture_output=True,
            timeout=8,
            shell=False,
        )
        if result.returncode == 0:
            time.sleep(1.0)
            return True
    except Exception:
        pass

    binary = shutil.which(app_name) or shutil.which(app_name.lower())
    if binary:
        try:
            subprocess.Popen(
                [binary],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            time.sleep(1.0)
            return True
        except Exception:
            pass

    return False


def _launch_linux(app_name: str) -> bool:
    """Launch an application on Linux without shell=True."""
    binary = (
        shutil.which(app_name)
        or shutil.which(app_name.lower())
        or shutil.which(app_name.lower().replace(" ", "-"))
        or shutil.which(app_name.lower().replace(" ", "_"))
    )
    if binary:
        try:
            subprocess.Popen(
                [binary],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            time.sleep(1.0)
            return True
        except Exception:
            pass

    try:
        subprocess.run(
            ["xdg-open", app_name],
            capture_output=True,
            timeout=5,
            shell=False,
        )
        return True
    except Exception:
        pass

    return False


_OS_LAUNCHERS = {
    "Windows": _launch_windows,
    "Darwin": _launch_macos,
    "Linux": _launch_linux,
}


def open_app(
    parameters: dict | None = None,
    response: Any | None = None,
    player: Any | None = None,
    session_memory: Any | None = None,
) -> str:
    """Open an application securely without shell=True."""
    app_name = (parameters or {}).get("app_name", "").strip()

    if not app_name:
        return "No application name provided."

    if _is_blocked(app_name):
        return f"Opening '{app_name}' is blocked for security reasons."

    launcher = _OS_LAUNCHERS.get(_SYSTEM)
    if launcher is None:
        return f"Unsupported operating system: {_SYSTEM}"

    normalized = _normalize(app_name)
    print(f"[open_app] Launching: '{app_name}' → '{normalized}' ({_SYSTEM})")

    if player:
        player.write_log(f"[open_app] {app_name}")

    try:
        if launcher(normalized):
            return f"Opened {app_name}."
        if normalized.lower() != app_name.lower():
            if launcher(app_name):
                return f"Opened {app_name}."
        return (
            f"Could not confirm that {app_name} launched. "
            f"It may still be loading, or it might not be installed."
        )
    except Exception as e:
        print(f"[open_app] Error: {e}")
        return f"Failed to open {app_name}: {e}"
