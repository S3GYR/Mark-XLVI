"""Main PyQt6 window for JARVIS."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from jarvis.ui.constants import C, DEFAULT_H, DEFAULT_W, MIN_H, MIN_W, qcol
from jarvis.ui.file_drop import FileDropZone
from jarvis.ui.hud import HudCanvas
from jarvis.ui.log_panel import LogWidget
from jarvis.ui.metric_bar import MetricBar
from jarvis.ui.metrics import SystemMetrics


class JarvisMainWindow(QMainWindow):
    """Refactored modular main window."""

    # Signals for external integration
    text_command = pyqtSignal(str)
    remote_clicked = pyqtSignal()
    mute_toggled = pyqtSignal(bool)

    def __init__(self, face_path: str | None = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("JARVIS")
        self.setMinimumSize(MIN_W, MIN_H)
        self.resize(DEFAULT_W, DEFAULT_H)

        self.muted = False
        self.current_file: str | None = None
        self.on_text_command: Callable[[str], None] | None = None
        self.on_remote_clicked: Callable | None = None

        self._metrics = SystemMetrics()
        self._central = QWidget()
        self.setCentralWidget(self._central)
        self._build_ui(face_path)

    def _build_ui(self, face_path: str | None) -> None:
        layout = QHBoxLayout(self._central)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # Left panel: metrics
        left = QVBoxLayout()
        left.setSpacing(8)
        self._cpu_bar = MetricBar("CPU", C.PRI)
        self._mem_bar = MetricBar("MEM", C.PRI)
        self._net_bar = MetricBar("NET", C.PRI)
        self._gpu_bar = MetricBar("GPU", C.PRI)
        self._tmp_bar = MetricBar("TMP", C.PRI)
        for bar in (self._cpu_bar, self._mem_bar, self._net_bar, self._gpu_bar, self._tmp_bar):
            left.addWidget(bar)
        left.addStretch()
        layout.addLayout(left)

        # Center: HUD + log
        center = QVBoxLayout()
        self._hud = HudCanvas(face_path)
        center.addWidget(self._hud, stretch=3)

        self._log = LogWidget()
        center.addWidget(self._log, stretch=2)

        # Input row
        row = QHBoxLayout()
        self._input = _CommandLine()
        self._input.command_entered.connect(self._send_command)
        row.addWidget(self._input, stretch=1)
        self._send_btn = QPushButton("Send")
        self._send_btn.setStyleSheet(f"background: {C.PRI}; color: {C.DARK}; font-weight: bold;")
        self._send_btn.clicked.connect(self._send_command)
        row.addWidget(self._send_btn)
        self._mute_btn = QPushButton("Mute")
        self._mute_btn.setCheckable(True)
        self._mute_btn.setStyleSheet(f"color: {C.MUTED};")
        self._mute_btn.toggled.connect(self._toggle_mute)
        row.addWidget(self._mute_btn)
        self._remote_btn = QPushButton("Remote")
        self._remote_btn.clicked.connect(self.remote_clicked.emit)
        row.addWidget(self._remote_btn)
        center.addLayout(row)
        layout.addLayout(center, stretch=3)

        # Right panel: file drop + status
        right = QVBoxLayout()
        self._drop = FileDropZone()
        self._drop.file_selected.connect(self._on_file_selected)
        right.addWidget(self._drop)
        self._status = QLabel("Ready")
        self._status.setStyleSheet(f"color: {C.TEXT_DIM}; font: 10px 'Courier New';")
        right.addWidget(self._status)
        right.addStretch()
        layout.addLayout(right)

        self._metrics_timer = QTimer(self)
        self._metrics_timer.timeout.connect(self._update_metrics)
        self._metrics_timer.start(1000)

        self.write_log("SYS: Modular JARVIS UI ready.")

    def _send_command(self) -> None:
        text = self._input.text().strip()
        if not text:
            return
        self._input.clear()
        self.write_log(f"YOU: {text}")
        if self.on_text_command:
            self.on_text_command(text)
        self.text_command.emit(text)

    def _toggle_mute(self, checked: bool) -> None:
        self.muted = checked
        self._hud.muted = checked
        self.mute_toggled.emit(checked)
        self.write_log("SYS: Microphone " + ("muted" if checked else "unmuted"))

    def _on_file_selected(self, path: str) -> None:
        self.current_file = path
        self.write_log(f"FILE: {path}")

    def _update_metrics(self) -> None:
        m = self._metrics.snapshot()
        self._cpu_bar.set_value(m["cpu"], f"{m['cpu']:.1f}%")
        self._mem_bar.set_value(m["memory"], f"{m['memory']:.1f}%")
        self._net_bar.set_value(min(m["network"] * 10, 100), f"{m['network']:.1f} MB/s")
        self._gpu_bar.set_value(m["gpu"] if m["gpu"] >= 0 else 0, f"{m['gpu']:.0f}%" if m["gpu"] >= 0 else "--")
        self._tmp_bar.set_value(m["temperature"] if m["temperature"] >= 0 else 0, f"{m['temperature']:.0f}°C" if m["temperature"] >= 0 else "--")

    def write_log(self, text: str) -> None:
        self._log.append_log(text)

    def set_state(self, state: str) -> None:
        self._hud.state = state
        self._status.setText(f"State: {state}")

    def closeEvent(self, event) -> None:
        self._metrics.stop()
        self._metrics_timer.stop()
        event.accept()


class _CommandLine(QWidget):
    """Command line with Enter key emission."""

    command_entered = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        from PyQt6.QtWidgets import QLineEdit
        self._line = QLineEdit(self)
        self._line.setPlaceholderText("Type a command...")
        self._line.setStyleSheet(f"""
            QLineEdit {{
                background: {C.PANEL};
                color: {C.TEXT};
                border: 1px solid {C.BORDER};
                border-radius: 4px;
                padding: 6px;
                font: 11px 'Courier New';
            }}
        """)
        self._line.returnPressed.connect(self._on_return)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._line)

    def _on_return(self) -> None:
        self.command_entered.emit(self._line.text())

    def text(self) -> str:
        return self._line.text()

    def clear(self) -> None:
        self._line.clear()
