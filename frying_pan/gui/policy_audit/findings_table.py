from __future__ import annotations

from PySide6.QtWidgets import QTableWidget


class FindingsTable(QTableWidget):
    def __init__(self) -> None:
        super().__init__(0, 6)
        self.setHorizontalHeaderLabels(
            ["Finding type", "Severity", "Rule", "Affected traffic", "Explanation", "Action"]
        )
