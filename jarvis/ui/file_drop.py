"""Drag-and-drop file zone widget."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

from jarvis.ui.constants import C


_FILE_ICONS = {
    "image": ("🖼", "#00d4ff"),
    "video": ("🎬", "#ff6b00"),
    "audio": ("🎵", "#cc44ff"),
    "pdf": ("📄", "#ff4444"),
    "word": ("📝", "#4488ff"),
    "excel": ("📊", "#44bb44"),
    "code": ("💻", "#ffcc00"),
    "archive": ("📦", "#ff8844"),
    "pptx": ("📊", "#ff6622"),
    "text": ("📃", "#aaaaaa"),
    "data": ("🔧", "#88ddff"),
    "unknown": ("📎", "#888888"),
}

_EXT_TO_CAT = {
    **dict.fromkeys(["jpg", "jpeg", "png", "gif", "webp", "bmp", "tiff", "svg", "ico"], "image"),
    **dict.fromkeys(["mp4", "avi", "mov", "mkv", "wmv", "flv", "webm", "m4v"], "video"),
    **dict.fromkeys(["mp3", "wav", "ogg", "m4a", "aac", "flac", "wma", "opus"], "audio"),
    **dict.fromkeys(["pdf"], "pdf"),
    **dict.fromkeys(["doc", "docx"], "word"),
    **dict.fromkeys(["xls", "xlsx", "ods"], "excel"),
    **dict.fromkeys(["ppt", "pptx"], "pptx"),
    **dict.fromkeys(
        ["py", "js", "ts", "jsx", "tsx", "html", "css", "java", "c", "cpp", "cs", "go", "rs", "rb", "php", "swift", "kt", "sh", "sql", "lua"],
        "code",
    ),
    **dict.fromkeys(["zip", "rar", "tar", "gz", "7z", "bz2", "xz"], "archive"),
    **dict.fromkeys(["txt", "md", "rst", "log"], "text"),
    **dict.fromkeys(["csv", "tsv", "json", "xml"], "data"),
}


def _file_category(path: Path) -> str:
    return _EXT_TO_CAT.get(path.suffix.lower().lstrip("."), "unknown")


def _fmt_size(size: int) -> str:
    if size < 1024:
        return f"{size} B"
    elif size < 1024**2:
        return f"{size/1024:.1f} KB"
    elif size < 1024**3:
        return f"{size/1024**2:.1f} MB"
    return f"{size/1024**3:.1f} GB"


class FileDropZone(QWidget):
    """Widget accepting drag-and-drop of files."""

    file_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(100)
        self._current_file: str | None = None
        self.setStyleSheet(f"""
            QWidget {{
                background: {C.PANEL};
                border: 2px dashed {C.BORDER};
                border-radius: 8px;
                color: {C.TEXT_DIM};
            }}
            QWidget:hover {{
                border-color: {C.PRI};
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        self._label = QLabel("Drop a file here\nor click to browse", self)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._label)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            self._set_file(path)

    def mouseReleaseEvent(self, event) -> None:
        from PyQt6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(self, "Select a file")
        if path:
            self._set_file(path)

    def _set_file(self, path: str) -> None:
        self._current_file = path
        p = Path(path)
        cat = _file_category(p)
        icon, _ = _FILE_ICONS.get(cat, _FILE_ICONS["unknown"])
        self._label.setText(f"{icon} {p.name}\n{_fmt_size(p.stat().st_size)}")
        self.file_selected.emit(path)

    def current_file(self) -> str | None:
        return self._current_file
