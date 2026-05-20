from __future__ import annotations

from PySide6.QtWidgets import QSplitter, QVBoxLayout, QWidget

from frying_pan.gui.migrate.mapping_table import MappingTable
from frying_pan.gui.migrate.source_tree_view import SourceTreeView
from frying_pan.gui.migrate.target_tree_view import TargetTreeView


class MigrationWorkspace(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        splitter = QSplitter()
        splitter.addWidget(SourceTreeView())
        splitter.addWidget(MappingTable())
        splitter.addWidget(TargetTreeView())
        layout.addWidget(splitter)
