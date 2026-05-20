from __future__ import annotations

from PySide6.QtWidgets import QSplitter, QVBoxLayout, QWidget

from frying_pan.gui.convert.conversion_mapping_view import ConversionMappingView
from frying_pan.gui.convert.vendor_source_view import VendorSourceView
from frying_pan.gui.placeholders import PlaceholderView


class ConversionWorkspace(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        splitter = QSplitter()
        splitter.addWidget(VendorSourceView())
        splitter.addWidget(ConversionMappingView())
        splitter.addWidget(
            PlaceholderView("Palo Normalized Preview", "Converted import package preview.")
        )
        layout.addWidget(splitter)
