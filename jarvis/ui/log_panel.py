"""Typewriter-style log panel widget."""

from __future__ import annotations

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QBrush, QFont, QTextCursor
from PyQt6.QtWidgets import QTextEdit

from jarvis.ui.constants import C, qcol


class LogWidget(QTextEdit):
    """Animated log panel with color-coded message tags."""

    _sig = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setFont(QFont("Courier New", 9))
        self.setStyleSheet(f"""
            QTextEdit {{
                background: {C.PANEL};
                color: {C.TEXT};
                border: 1px solid {C.BORDER};
                border-radius: 4px;
                padding: 6px;
                selection-background-color: {C.PRI_GHO};
            }}
            QScrollBar:vertical {{
                background: {C.BG};
                width: 8px;
                border: none;
            }}
            QScrollBar::handle:vertical {{
                background: {C.BORDER_B};
                border-radius: 4px;
                min-height: 20px;
            }}
        """)
        self._queue: list[str] = []
        self._typing = False
        self._text = ""
        self._pos = 0
        self._tag = "sys"
        self._tmr = QTimer(self)
        self._tmr.timeout.connect(self._step)
        self._sig.connect(self._enqueue)

    def append_log(self, text: str) -> None:
        self._sig.emit(text)

    def _enqueue(self, text: str) -> None:
        self._queue.append(text)
        if not self._typing:
            self._next()

    def _next(self) -> None:
        if not self._queue:
            self._typing = False
            return
        self._typing = True
        self._text = self._queue.pop(0)
        self._pos = 0
        tl = self._text.lower()
        if tl.startswith("you:"):
            self._tag = "you"
        elif tl.startswith("jarvis:"):
            self._tag = "ai"
        elif tl.startswith("file:"):
            self._tag = "file"
        elif "err" in tl:
            self._tag = "err"
        else:
            self._tag = "sys"
        self._tmr.start(6)

    def _step(self) -> None:
        if self._pos < len(self._text):
            ch = self._text[self._pos]
            cur = self.textCursor()
            fmt = cur.charFormat()
            col = {
                "you": QBrush(qcol(C.WHITE)),
                "ai": QBrush(qcol(C.PRI)),
                "err": QBrush(qcol(C.RED)),
                "file": QBrush(qcol(C.GREEN)),
                "sys": QBrush(qcol(C.ACC2)),
            }.get(self._tag, QBrush(qcol(C.TEXT)))
            fmt.setForeground(col)
            cur.movePosition(QTextCursor.MoveOperation.End)
            cur.insertText(ch, fmt)
            self.setTextCursor(cur)
            self.ensureCursorVisible()
            self._pos += 1
        else:
            self._tmr.stop()
            cur = self.textCursor()
            cur.movePosition(QTextCursor.MoveOperation.End)
            cur.insertText("\n")
            self.setTextCursor(cur)
            self.ensureCursorVisible()
            QTimer.singleShot(20, self._next)
