from __future__ import annotations

from PySide6.QtGui import QStandardItem, QStandardItemModel

from frying_pan.normalized.config import NormalizedConfig


def build_source_tree_model(config: NormalizedConfig) -> QStandardItemModel:
    model = QStandardItemModel()
    model.setHorizontalHeaderLabels(["Source Inventory"])
    root = model.invisibleRootItem()
    for scope in config.scopes:
        root.appendRow(QStandardItem(f"{scope.scope_type}: {scope.name}"))
    return model
