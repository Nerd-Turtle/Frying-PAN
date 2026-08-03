from __future__ import annotations

from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QGridLayout,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from frying_pan.analysis.inventory import summarize_inventory
from frying_pan.normalized.config import NormalizedConfig


class InventoryView(QWidget):
    def __init__(self, config: NormalizedConfig | None = None) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        title = QLabel("Inventory")
        title.setObjectName("PageTitle")
        self.summary_label = QLabel("Load a supported configuration source to inspect inventory.")
        self.summary_label.setObjectName("InventorySummary")
        self.summary_label.setProperty("muted", True)
        layout.addWidget(title)
        layout.addWidget(self.summary_label)

        metrics_card = QFrame()
        metrics_card.setObjectName("WorkbenchCard")
        metrics_layout = QGridLayout(metrics_card)
        metrics_layout.setContentsMargins(16, 12, 16, 12)
        metrics_layout.setHorizontalSpacing(28)
        self.metric_labels: dict[str, QLabel] = {}
        for column, metric in enumerate(
            ("Scopes", "Entities", "Security rules", "References", "Unresolved", "Warnings")
        ):
            metric_widget = QWidget()
            metric_layout = QVBoxLayout(metric_widget)
            metric_layout.setContentsMargins(0, 0, 0, 0)
            value_label = QLabel("0")
            value_label.setObjectName("MetricValue")
            name_label = QLabel(metric)
            name_label.setProperty("muted", True)
            metric_layout.addWidget(value_label)
            metric_layout.addWidget(name_label)
            metrics_layout.addWidget(metric_widget, 0, column)
            self.metric_labels[metric] = value_label
        layout.addWidget(metrics_card)

        self.counts_table = QTableWidget(0, 2)
        self.counts_table.setHorizontalHeaderLabels(["Metric", "Count"])
        self.scopes_table = QTableWidget(0, 3)
        self.scopes_table.setHorizontalHeaderLabels(["Scope", "Type", "Path"])
        self.objects_table = QTableWidget(0, 3)
        self.objects_table.setHorizontalHeaderLabels(["Name", "Type", "Scope"])
        self.rules_table = QTableWidget(0, 4)
        self.rules_table.setHorizontalHeaderLabels(["Name", "Rulebase", "Scope", "Action"])

        for table in (
            self.counts_table,
            self.scopes_table,
            self.objects_table,
            self.rules_table,
        ):
            table.setAlternatingRowColors(True)
            table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
            table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
            table.verticalHeader().setVisible(False)
            table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        self.inventory_tabs = QTabWidget()
        self.inventory_tabs.setDocumentMode(True)
        self.inventory_tabs.addTab(self.objects_table, "Objects")
        self.inventory_tabs.addTab(self.rules_table, "Security Rules")
        self.inventory_tabs.addTab(self.scopes_table, "Scopes")
        self.inventory_tabs.addTab(self.counts_table, "Summary")
        layout.addWidget(self.inventory_tabs, 1)

        if config is not None:
            self.set_config(config)

    def set_config(self, config: NormalizedConfig) -> None:
        summary = summarize_inventory(config)
        self.summary_label.setText(
            f"{summary.source_type}: {summary.entity_count} objects, "
            f"{summary.security_rule_count} security rules"
        )
        self._set_counts(
            {
                "Scopes": summary.scope_count,
                "Entities": summary.entity_count,
                "Security rules": summary.security_rule_count,
                "References": summary.reference_count,
                "Unresolved references": summary.unresolved_reference_count,
                "Warnings": summary.warning_count,
            }
        )
        for name, value in (
            ("Scopes", summary.scope_count),
            ("Entities", summary.entity_count),
            ("Security rules", summary.security_rule_count),
            ("References", summary.reference_count),
            ("Unresolved", summary.unresolved_reference_count),
            ("Warnings", summary.warning_count),
        ):
            self.metric_labels[name].setText(str(value))
        self._set_scopes(config)
        self._set_objects(config)
        self._set_rules(config)

    def _set_counts(self, counts: dict[str, int]) -> None:
        self.counts_table.setRowCount(0)
        for metric, count in counts.items():
            row = self.counts_table.rowCount()
            self.counts_table.insertRow(row)
            self.counts_table.setItem(row, 0, QTableWidgetItem(metric))
            self.counts_table.setItem(row, 1, QTableWidgetItem(str(count)))

    def _set_scopes(self, config: NormalizedConfig) -> None:
        self.scopes_table.setRowCount(0)
        for scope in config.scopes:
            row = self.scopes_table.rowCount()
            self.scopes_table.insertRow(row)
            self.scopes_table.setItem(row, 0, QTableWidgetItem(scope.name))
            self.scopes_table.setItem(row, 1, QTableWidgetItem(scope.scope_type.value))
            self.scopes_table.setItem(row, 2, QTableWidgetItem(scope.path))

    def _set_objects(self, config: NormalizedConfig) -> None:
        self.objects_table.setRowCount(0)
        for entity in config.entities:
            row = self.objects_table.rowCount()
            self.objects_table.insertRow(row)
            self.objects_table.setItem(row, 0, QTableWidgetItem(entity.name))
            self.objects_table.setItem(row, 1, QTableWidgetItem(entity.entity_type.value))
            self.objects_table.setItem(row, 2, QTableWidgetItem(entity.scope_path))

    def _set_rules(self, config: NormalizedConfig) -> None:
        self.rules_table.setRowCount(0)
        for rule in config.security_rules:
            row = self.rules_table.rowCount()
            self.rules_table.insertRow(row)
            self.rules_table.setItem(row, 0, QTableWidgetItem(rule.name))
            self.rules_table.setItem(row, 1, QTableWidgetItem(rule.rulebase_type.value))
            self.rules_table.setItem(row, 2, QTableWidgetItem(rule.scope_path))
            self.rules_table.setItem(row, 3, QTableWidgetItem(rule.action.value))
