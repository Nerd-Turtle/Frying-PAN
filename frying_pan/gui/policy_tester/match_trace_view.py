from __future__ import annotations

from PySide6.QtWidgets import QTableWidget, QTableWidgetItem

from frying_pan.policy.match.result import PolicyMatchResult


class MatchTraceView(QTableWidget):
    def __init__(self) -> None:
        super().__init__(0, 5)
        self.setHorizontalHeaderLabels(["Rule", "Matched", "Action", "Reason", "Warnings"])

    def set_result(self, result: PolicyMatchResult) -> None:
        self.setRowCount(len(result.trace))
        for row, step in enumerate(result.trace):
            values = [
                step.rule_name,
                "yes" if step.matched else "no",
                step.action.value if step.action else "",
                step.reason,
                "; ".join(step.warnings),
            ]
            for column, value in enumerate(values):
                self.setItem(row, column, QTableWidgetItem(value))
        self.resizeColumnsToContents()
