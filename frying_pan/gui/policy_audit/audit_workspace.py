from __future__ import annotations

from PySide6.QtWidgets import QLabel, QSplitter, QVBoxLayout, QWidget

from frying_pan.gui.policy_audit.finding_detail_view import FindingDetailView
from frying_pan.gui.policy_audit.findings_table import FindingsTable
from frying_pan.policy.audit.findings import PolicyAuditResult


class AuditWorkspace(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        splitter = QSplitter()
        self.summary_label = QLabel("Policy Audit: no result loaded")
        self.summary_label.setWordWrap(True)
        self.findings_table = FindingsTable()
        self.detail_view = FindingDetailView()
        splitter.addWidget(self.summary_label)
        splitter.addWidget(self.findings_table)
        splitter.addWidget(self.detail_view)
        layout.addWidget(splitter)

    def set_result(self, result: PolicyAuditResult) -> None:
        self.summary_label.setText(
            f"Scope: {result.scope_path or 'all audited scopes'}\n"
            f"Audited rules: {result.audited_rule_count}\n"
            f"Findings: {result.finding_count}\n"
            f"Warnings: {len(result.warnings)}"
        )
        self.findings_table.set_result(result)
        self.detail_view.set_finding(result.findings[0] if result.findings else None)
