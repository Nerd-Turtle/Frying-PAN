from __future__ import annotations

from PySide6.QtWidgets import QTableWidget, QTableWidgetItem

from frying_pan.workflows.migrate.migration_plan import MigrationPlan


class MappingTable(QTableWidget):
    def __init__(self) -> None:
        super().__init__(0, 4)
        self.setHorizontalHeaderLabels(["Action", "Source", "Target", "Status"])

    def set_plan(self, plan: MigrationPlan) -> None:
        self.setRowCount(len(plan.decisions))
        for row, decision in enumerate(plan.decisions):
            values = [
                decision.action.value,
                decision.source_ref,
                decision.target_ref or "",
                decision.status.value,
            ]
            for column, value in enumerate(values):
                self.setItem(row, column, QTableWidgetItem(value))
        self.resizeColumnsToContents()
