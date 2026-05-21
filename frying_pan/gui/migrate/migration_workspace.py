from __future__ import annotations

from PySide6.QtWidgets import QLabel, QSplitter, QVBoxLayout, QWidget

from frying_pan.gui.migrate.mapping_table import MappingTable
from frying_pan.gui.migrate.source_tree_view import SourceTreeView
from frying_pan.gui.migrate.target_tree_view import TargetTreeView
from frying_pan.workflows.migrate.migration_plan import MigrationPlan


class MigrationWorkspace(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        splitter = QSplitter()
        self.summary_label = QLabel("Migration Plan: no staged plan loaded")
        self.summary_label.setWordWrap(True)
        splitter.addWidget(SourceTreeView())
        self.mapping_table = MappingTable()
        splitter.addWidget(self.mapping_table)
        splitter.addWidget(TargetTreeView())
        layout.addWidget(splitter)
        layout.addWidget(self.summary_label)

    def set_plan(self, plan: MigrationPlan) -> None:
        self.summary_label.setText(
            f"Status: {plan.status.value}\n"
            f"Mappings: {plan.mapping_count}\n"
            f"Decisions: {plan.decision_count}\n"
            f"Validation messages: {len(plan.validation.messages)}"
        )
        self.mapping_table.set_plan(plan)
