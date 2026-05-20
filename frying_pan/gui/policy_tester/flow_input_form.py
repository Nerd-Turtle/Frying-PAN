from __future__ import annotations

from PySide6.QtWidgets import QFormLayout, QLineEdit, QWidget


class FlowInputForm(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QFormLayout(self)
        for label in (
            "Source zone",
            "Destination zone",
            "Source IP",
            "Destination IP",
            "Protocol",
            "Destination port",
            "Application",
            "User",
            "URL category",
        ):
            layout.addRow(label, QLineEdit())
