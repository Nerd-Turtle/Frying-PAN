from __future__ import annotations

from PySide6.QtWidgets import QSplitter, QVBoxLayout, QWidget

from frying_pan.gui.placeholders import PlaceholderView
from frying_pan.gui.policy_audit.finding_detail_view import FindingDetailView
from frying_pan.gui.policy_audit.findings_table import FindingsTable


class AuditWorkspace(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        splitter = QSplitter()
        splitter.addWidget(
            PlaceholderView("Scope / Rulebase", "Select scope and rulebase for audit.")
        )
        splitter.addWidget(FindingsTable())
        splitter.addWidget(FindingDetailView())
        layout.addWidget(splitter)
