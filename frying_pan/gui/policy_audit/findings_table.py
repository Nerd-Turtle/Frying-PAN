from __future__ import annotations

from PySide6.QtWidgets import QTableWidget, QTableWidgetItem

from frying_pan.policy.audit.findings import PolicyAuditResult


class FindingsTable(QTableWidget):
    def __init__(self) -> None:
        super().__init__(0, 6)
        self.setHorizontalHeaderLabels(
            ["ID", "Finding type", "Severity", "Scope", "Rules", "Explanation"]
        )

    def set_result(self, result: PolicyAuditResult) -> None:
        self.setRowCount(len(result.findings))
        for row, finding in enumerate(result.findings):
            values = [
                finding.finding_id or "",
                finding.finding_type.value,
                finding.severity.value,
                finding.scope_or_rulebase,
                ", ".join(finding.affected_rules),
                finding.explanation,
            ]
            for column, value in enumerate(values):
                self.setItem(row, column, QTableWidgetItem(value))
        self.resizeColumnsToContents()
