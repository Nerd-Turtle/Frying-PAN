from __future__ import annotations

from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from frying_pan.workflows.convert.converted_import import ConvertedImportPackage


class ConversionMappingView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Type", "Severity", "Code", "Message"])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

    def set_package(self, package: ConvertedImportPackage) -> None:
        rows = len(package.warnings) + len(package.unsupported_features)
        self.table.setRowCount(rows)
        row = 0
        for warning in package.warnings:
            self._set_row(
                row,
                "warning",
                warning.severity.value,
                warning.code,
                warning.message,
            )
            row += 1
        for feature in package.unsupported_features:
            self._set_row(
                row,
                "unsupported",
                "high",
                feature.feature,
                feature.notes or "Review required.",
            )
            row += 1

    def _set_row(
        self, row: int, item_type: str, severity: str, code: str, message: str
    ) -> None:
        for column, value in enumerate([item_type, severity, code, message]):
            self.table.setItem(row, column, QTableWidgetItem(value))
