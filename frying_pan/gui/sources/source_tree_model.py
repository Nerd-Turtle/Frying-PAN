from __future__ import annotations

from PySide6.QtGui import QStandardItem, QStandardItemModel

from frying_pan.normalized.config import NormalizedConfig


def build_source_tree_model(config: NormalizedConfig) -> QStandardItemModel:
    model = QStandardItemModel()
    model.setHorizontalHeaderLabels(["Source Inventory"])
    root = model.invisibleRootItem()
    scopes_item = QStandardItem("Scopes")
    for scope in config.scopes:
        scopes_item.appendRow(QStandardItem(f"{scope.scope_type.value}: {scope.name}"))
    root.appendRow(scopes_item)

    objects_item = QStandardItem("Objects")
    for entity in config.entities:
        objects_item.appendRow(
            QStandardItem(f"{entity.entity_type.value}: {entity.name} [{entity.scope_path}]")
        )
    root.appendRow(objects_item)

    rules_item = QStandardItem("Security Rules")
    for rule in config.security_rules:
        rules_item.appendRow(
            QStandardItem(
                f"{rule.rulebase_type.value}: {rule.name} [{rule.scope_path}] {rule.action.value}"
            )
        )
    root.appendRow(rules_item)
    return model
