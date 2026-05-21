from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from frying_pan.policy.audit.findings import AuditFinding


class FindingDetailView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        self.title_label = QLabel("Finding Details")
        self.body_label = QLabel("Select or load a policy audit finding.")
        self.body_label.setWordWrap(True)
        layout.addWidget(self.title_label)
        layout.addWidget(self.body_label)
        layout.addStretch()

    def set_finding(self, finding: AuditFinding | None) -> None:
        if finding is None:
            self.body_label.setText("No finding selected.")
            return
        self.body_label.setText(
            "\n".join(
                [
                    f"Type: {finding.finding_type.value}",
                    f"Severity: {finding.severity.value}",
                    f"Rules: {', '.join(finding.affected_rules) or 'None'}",
                    f"Explanation: {finding.explanation}",
                    f"Recommendation: {finding.recommendation or 'Review manually.'}",
                    f"Warnings: {len(finding.warnings)}",
                ]
            )
        )
