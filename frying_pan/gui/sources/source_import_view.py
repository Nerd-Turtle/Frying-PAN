from __future__ import annotations

from PySide6.QtWidgets import QPushButton, QVBoxLayout, QWidget

from frying_pan.gui.placeholders import PlaceholderView


class SourceImportView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(
            PlaceholderView(
                "Sources",
                "Import Panorama XML, standalone firewall XML, "
                "or future vendor inputs into a local project.",
            )
        )
        layout.addWidget(QPushButton("Import Source"))
        layout.addStretch()
