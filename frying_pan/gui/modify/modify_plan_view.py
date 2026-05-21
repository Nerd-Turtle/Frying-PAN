from __future__ import annotations

from PySide6.QtWidgets import QTableWidget, QTableWidgetItem

from frying_pan.workflows.modify.modify_plan import ModificationPlan


class ModifyPlanView(QTableWidget):
    def __init__(self) -> None:
        super().__init__(0, 5)
        self.setHorizontalHeaderLabels(["Action", "Source", "Target", "Status", "Warnings"])

    def set_plan(self, plan: ModificationPlan) -> None:
        self.setRowCount(len(plan.decisions))
        for row, decision in enumerate(plan.decisions):
            values = [
                decision.action.value,
                decision.source_ref,
                decision.target_ref or "",
                decision.status.value,
                "; ".join(decision.warnings),
            ]
            for column, value in enumerate(values):
                self.setItem(row, column, QTableWidgetItem(value))
        self.resizeColumnsToContents()
