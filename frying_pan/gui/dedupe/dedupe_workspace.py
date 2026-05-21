from __future__ import annotations

from PySide6.QtWidgets import (
    QLabel,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from frying_pan.analysis.dedupe_models import DedupeAnalysisResult, DedupeFinding


class DedupeFindingsTable(QTableWidget):
    def __init__(self) -> None:
        super().__init__(0, 6)
        self.setHorizontalHeaderLabels(
            ["ID", "Type", "Severity", "Object type", "Objects", "Scopes"]
        )

    def set_result(self, result: DedupeAnalysisResult) -> None:
        self.setRowCount(len(result.findings))
        for row, finding in enumerate(result.findings):
            values = [
                finding.finding_id or "",
                finding.finding_type.value,
                finding.severity.value,
                finding.object_type,
                ", ".join(finding.object_names),
                ", ".join(finding.scopes),
            ]
            for column, value in enumerate(values):
                self.setItem(row, column, QTableWidgetItem(value))
        self.resizeColumnsToContents()


class DedupeFindingDetail(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        self.body_label = QLabel("No dedupe/conflict finding selected.")
        self.body_label.setWordWrap(True)
        layout.addWidget(self.body_label)
        layout.addStretch()

    def set_finding(self, finding: DedupeFinding | None) -> None:
        if finding is None:
            self.body_label.setText("No dedupe/conflict finding selected.")
            return
        self.body_label.setText(
            "\n".join(
                [
                    f"Type: {finding.finding_type.value}",
                    f"Severity: {finding.severity.value}",
                    f"Objects: {', '.join(finding.object_names) or 'None'}",
                    f"Scopes: {', '.join(finding.scopes) or 'None'}",
                    f"Explanation: {finding.explanation}",
                    f"Recommendation: {finding.recommendation or 'Review manually.'}",
                    f"Warnings: {len(finding.warnings)}",
                ]
            )
        )


class DedupeWorkspace(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        splitter = QSplitter()
        self.summary_label = QLabel("Dedupe/Conflict Analysis: no result loaded")
        self.summary_label.setWordWrap(True)
        self.findings_table = DedupeFindingsTable()
        self.detail_view = DedupeFindingDetail()
        splitter.addWidget(self.summary_label)
        splitter.addWidget(self.findings_table)
        splitter.addWidget(self.detail_view)
        layout.addWidget(splitter)

    def set_result(self, result: DedupeAnalysisResult) -> None:
        self.summary_label.setText(
            f"Analyzed objects: {result.analyzed_object_count}\n"
            f"Findings: {result.finding_count}\n"
            f"Warnings: {len(result.warnings)}"
        )
        self.findings_table.set_result(result)
        self.detail_view.set_finding(result.findings[0] if result.findings else None)
