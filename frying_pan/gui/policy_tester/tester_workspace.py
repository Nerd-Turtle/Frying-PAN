from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from frying_pan.gui.policy_tester.flow_input_form import FlowInputForm
from frying_pan.gui.policy_tester.match_trace_view import MatchTraceView
from frying_pan.normalized.config import NormalizedConfig
from frying_pan.policy.match.result import PolicyMatchResult


class PolicyTesterWorkspace(QWidget):
    run_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        header = QHBoxLayout()
        heading = QVBoxLayout()
        title = QLabel("Policy Tester")
        title.setObjectName("PageTitle")
        self.source_label = QLabel("Load a configuration source to run a test flow.")
        self.source_label.setObjectName("PageSubtitle")
        heading.addWidget(title)
        heading.addWidget(self.source_label)
        header.addLayout(heading, 1)
        scope_label = QLabel("Scope")
        scope_label.setProperty("muted", True)
        self.scope_combo = QComboBox()
        self.scope_combo.setMinimumWidth(220)
        self.run_button = QPushButton("Run Policy Test")
        self.run_button.setProperty("primary", True)
        self.run_button.setEnabled(False)
        header.addWidget(scope_label)
        header.addWidget(self.scope_combo)
        header.addWidget(self.run_button)
        layout.addLayout(header)

        splitter = QSplitter()
        self.flow_input = FlowInputForm()
        self.result_label = QLabel("Matched rule: none")
        self.result_label.setWordWrap(True)
        self.trace_view = MatchTraceView()
        splitter.addWidget(self.flow_input)
        splitter.addWidget(self.result_label)
        splitter.addWidget(self.trace_view)
        layout.addWidget(splitter)
        self.run_button.clicked.connect(self.run_requested)

    def set_config(self, config: NormalizedConfig, source_name: str) -> None:
        self.source_label.setText(source_name)
        self.scope_combo.clear()
        self.scope_combo.addItem("All parsed scopes", None)
        for scope in config.scopes:
            self.scope_combo.addItem(scope.path, scope.path)
        self.run_button.setEnabled(True)

    def selected_scope(self) -> str | None:
        return self.scope_combo.currentData()

    def set_result(self, result: PolicyMatchResult) -> None:
        matched_rule = result.matched_rule.name if result.matched_rule else "none"
        self.result_label.setText(
            f"Matched rule: {matched_rule}\n"
            f"Action: {result.action}\n"
            f"Warnings: {len(result.warnings)}"
        )
        self.trace_view.set_result(result)
