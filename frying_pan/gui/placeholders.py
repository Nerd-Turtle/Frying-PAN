from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class PlaceholderView(QWidget):
    def __init__(self, title: str, body: str) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        title_label = QLabel(title)
        title_label.setObjectName("WorkspaceTitle")
        body_label = QLabel(body)
        body_label.setWordWrap(True)
        body_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addWidget(title_label)
        layout.addWidget(body_label)
        layout.addStretch()
