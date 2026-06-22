"""HUD face visualization widget."""

from __future__ import annotations

import math
import random
import time

from PyQt6.QtCore import Qt, QTimer, QRectF
from PyQt6.QtGui import QBrush, QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import QWidget

from jarvis.ui.constants import C, qcol


class HudCanvas(QWidget):
    """Animated circular HUD showing assistant state."""

    def __init__(self, face_path: str | None = None, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent)
        self.setMinimumSize(300, 300)
        self.setSizePolicy(
            self.sizePolicy().Policy.Expanding,
            self.sizePolicy().Policy.Expanding,
        )
        self.muted = False
        self.speaking = False
        self.state = "INITIALISING"
        self._tick = 0
        self._halo = 55.0
        self._scale = 1.0
        self._last_t = time.time()
        self._face_color = QColor(0, 60, 110)
        self._face_path = face_path
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._step)
        self._timer.start(50)

    def _step(self) -> None:
        self._tick += 1
        now = time.time()
        if now - self._last_t > (0.2 if self.speaking else 0.6):
            if self.speaking:
                self._scale = random.uniform(1.04, 1.10)
                self._halo = random.uniform(140, 180)
            elif self.muted:
                self._scale = random.uniform(0.998, 1.002)
                self._halo = random.uniform(15, 28)
            else:
                self._scale = random.uniform(1.001, 1.008)
                self._halo = random.uniform(48, 68)
            self._last_t = now
        self.update()

    def paintEvent(self, _) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), qcol(C.BG))

        W, H = self.width(), self.height()
        cx, cy = W / 2, H / 2
        fw = min(W, H)
        r_face = int(fw * 0.27 * self._scale)

        # Outer rings
        p.setPen(QPen(qcol(C.PRI, int(self._halo * 0.5)), 2))
        p.setBrush(Qt.BrushStyle.NoBrush)
        for r in [fw * 0.45, fw * 0.38]:
            p.drawEllipse(QRectF(cx - r, cy - r, r * 2, r * 2))

        # Face orb
        for i in range(8, 0, -1):
            r2 = int(r_face * i / 8)
            frc = i / 8
            a = max(0, min(255, int(self._halo * 1.1 * frc)))
            color = QColor(200, 0, 50) if self.muted else self._face_color
            p.setBrush(
                QBrush(
                    QColor(
                        int(color.red() * frc),
                        int(color.green() * frc),
                        int(color.blue() * frc),
                        a,
                    )
                )
            )
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QRectF(cx - r2, cy - r2, r2 * 2, r2 * 2))

        # Status label
        sy = cy + fw * 0.40
        if self.muted:
            txt, col = "⊘  MUTED", qcol(C.MUTED)
        elif self.speaking:
            txt, col = "●  SPEAKING", qcol(C.ACC)
        elif self.state == "THINKING":
            txt, col = "◈  THINKING", qcol(C.ACC2)
        elif self.state == "LISTENING":
            txt, col = "●  LISTENING", qcol(C.GREEN)
        else:
            txt, col = f"●  {self.state}", qcol(C.PRI)

        p.setPen(QPen(col, 1))
        p.setFont(QFont("Courier New", 11, QFont.Weight.Bold))
        p.drawText(QRectF(0, sy, W, 26), Qt.AlignmentFlag.AlignCenter, txt)

        # Mini waveform
        wy = sy + 30
        N, bw = 20, 8
        wx0 = (W - N * bw) / 2
        for i in range(N):
            if self.muted:
                hgt = 2
                cl = qcol(C.MUTED)
            elif self.speaking:
                hgt = random.randint(3, 18)
                cl = qcol(C.PRI) if hgt > 10 else qcol(C.PRI_DIM)
            else:
                hgt = int(3 + 2 * math.sin(self._tick * 0.09 + i * 0.6))
                cl = qcol(C.BORDER_B)
            p.fillRect(QRectF(wx0 + i * bw, wy + 20 - hgt, bw - 1, hgt), cl)
