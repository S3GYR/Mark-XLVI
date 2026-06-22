"""Tests for atomic UI widgets."""

from __future__ import annotations

import pytest
from PyQt6.QtCore import Qt

from jarvis.ui.constants import C, DEFAULT_H, DEFAULT_W
from jarvis.ui.file_drop import FileDropZone
from jarvis.ui.hud import HudCanvas
from jarvis.ui.log_panel import LogWidget
from jarvis.ui.main_window import JarvisMainWindow
from jarvis.ui.metric_bar import MetricBar


@pytest.fixture
def window(qtbot):
    """Create the main window for testing."""
    from PyQt6.QtWidgets import QApplication

    QApplication.instance() or QApplication([])
    w = JarvisMainWindow()
    qtbot.addWidget(w)
    return w


def test_constants():
    """UI constants are populated."""
    assert C.PRI == "#00d4ff"
    assert DEFAULT_W > 0
    assert DEFAULT_H > 0


def test_metric_bar(qtbot):
    """MetricBar accepts value updates."""
    bar = MetricBar("CPU", C.PRI)
    qtbot.addWidget(bar)
    bar.set_value(75.0, "75%")
    assert bar._value == 75.0
    assert bar._text == "75%"


def test_log_widget(qtbot):
    """LogWidget appends text."""
    log = LogWidget()
    qtbot.addWidget(log)
    log.append_log("test message")
    assert "test message" in log.toPlainText()


def test_file_drop_zone(qtbot):
    """FileDropZone has expected label."""
    drop = FileDropZone()
    qtbot.addWidget(drop)
    assert drop._label is not None


def test_hud_canvas(qtbot):
    """HudCanvas can update state."""
    hud = HudCanvas()
    qtbot.addWidget(hud)
    hud.state = "LISTENING"
    assert hud.state == "LISTENING"


def test_main_window_title(window: JarvisMainWindow):
    """Main window has the expected title."""
    assert "JARVIS" in window.windowTitle()


def test_main_window_set_state(window: JarvisMainWindow):
    """Main window state updates HUD and status."""
    window.set_state("THINKING")
    assert window._hud.state == "THINKING"
    assert "THINKING" in window._status.text()


def test_main_window_log(window: JarvisMainWindow):
    """Main window log widget receives text."""
    window.write_log("hello")
    assert "hello" in window._log.toPlainText()
