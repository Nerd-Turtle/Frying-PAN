from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from frying_pan.workflows.convert.converted_import import ConvertedImportPackage


class VendorSourceView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        title = QLabel("Vendor Source")
        title.setObjectName("WorkspaceTitle")
        self.status_label = QLabel("No converted package loaded.")
        self.status_label.setWordWrap(True)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addWidget(title)
        layout.addWidget(self.status_label)
        layout.addStretch()

    def set_package(self, package: ConvertedImportPackage) -> None:
        self.status_label.setText(
            "\n".join(
                [
                    f"Name: {package.name}",
                    f"Format: {package.source_format}",
                    f"Path: {package.source_path or 'unknown'}",
                    f"Validation errors: {len(package.validation.errors)}",
                    f"Validation warnings: {len(package.validation.warnings)}",
                ]
            )
        )
