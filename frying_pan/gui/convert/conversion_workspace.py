from __future__ import annotations

from PySide6.QtWidgets import QLabel, QSplitter, QVBoxLayout, QWidget

from frying_pan.gui.convert.conversion_mapping_view import ConversionMappingView
from frying_pan.gui.convert.vendor_source_view import VendorSourceView
from frying_pan.workflows.convert.converted_import import ConvertedImportPackage


class ConversionWorkspace(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        splitter = QSplitter()
        self.source_view = VendorSourceView()
        self.mapping_view = ConversionMappingView()
        self.preview_label = QLabel("No normalized package loaded.")
        self.preview_label.setWordWrap(True)
        splitter.addWidget(self.source_view)
        splitter.addWidget(self.mapping_view)
        splitter.addWidget(self.preview_label)
        layout.addWidget(splitter)

    def set_package(self, package: ConvertedImportPackage) -> None:
        self.source_view.set_package(package)
        self.mapping_view.set_package(package)
        self.preview_label.setText(
            "\n".join(
                [
                    "Palo Normalized Preview",
                    f"Scopes: {package.scope_count}",
                    f"Entities: {package.entity_count}",
                    f"Security rules: {package.security_rule_count}",
                    f"References: {len(package.normalized_config.references)}",
                    f"Unsupported features: {package.unsupported_count}",
                ]
            )
        )
