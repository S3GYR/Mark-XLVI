"""Desktop GUI entry point using PyQt6."""

from __future__ import annotations

import asyncio
import signal
import sys
from typing import Any

from PyQt6.QtWidgets import QApplication

from jarvis.config.settings import get_settings
from jarvis.core.live_session import GeminiLiveSession
from jarvis.core.player import Player
from jarvis.observability.logger import configure_logging, get_logger
from jarvis.observability.tracing import configure_tracing

logger = get_logger(__name__)


def start_gui_app() -> int:
    """Start the PyQt6 GUI with the modular live session."""
    configure_logging()
    configure_tracing()
    settings = get_settings()

    app = QApplication(sys.argv)
    app.setApplicationName("JARVIS")
    app.setApplicationVersion("46.0.0")

    # Use the modular main window
    from jarvis.ui.main_window import JarvisMainWindow

    window = JarvisMainWindow()
    player = _QtPlayerAdapter(window)
    session = GeminiLiveSession(player, settings)

    window.text_command.connect(lambda text: session.on_text_command(text))
    window.remote_clicked.connect(lambda: player.write_log("SYS: Remote control requested"))
    window.mute_toggled.connect(lambda muted: player.write_log(f"SYS: Muted={muted}"))

    # Run session in background asyncio loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    def shutdown() -> None:
        logger.info("gui_shutdown_requested")
        loop.call_soon_threadsafe(loop.stop)

    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda _s, _f: shutdown())

    async def _run_session() -> None:
        try:
            await session.start()
        except Exception as e:
            logger.error("session_error", error=str(e))
            player.write_log(f"Session error: {e}")

    def _start_loop() -> None:
        loop.run_until_complete(_run_session())

    import threading
    threading.Thread(target=_start_loop, daemon=True).start()

    window.show()
    return app.exec()


class _QtPlayerAdapter(Player):
    """Adapter making the legacy Qt UI compatible with the Player protocol."""

    def __init__(self, window: Any):
        self._window = window

    def write_log(self, text: str) -> None:
        self._window.write_log(text)

    def set_state(self, state: str) -> None:
        self._window.set_state(state)

    def request_confirmation(self, message: str) -> bool:
        from PyQt6.QtWidgets import QMessageBox

        reply = QMessageBox.question(
            self._window,
            "Confirmation required",
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        return reply == QMessageBox.StandardButton.Yes

    @property
    def muted(self) -> bool:
        return getattr(self._window, "muted", False)

    @property
    def current_file(self) -> str | None:
        return getattr(self._window, "current_file", None)

    def speak(self, text: str) -> None:
        # Speaking is handled by the session itself
        logger.info("speak_requested", text=text)
