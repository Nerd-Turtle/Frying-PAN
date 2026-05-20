from __future__ import annotations

from PySide6.QtWidgets import QTableWidget, QTableWidgetItem


class MappingTable(QTableWidget):
    def __init__(self) -> None:
        super().__init__(0, 4)
        self.setHorizontalHeaderLabels(["Action", "Source", "Target", "Status"])
        self.insertRow(0)
        self.setItem(0, 0, QTableWidgetItem("staged decisions"))
        self.setItem(0, 3, QTableWidgetItem("placeholder"))
