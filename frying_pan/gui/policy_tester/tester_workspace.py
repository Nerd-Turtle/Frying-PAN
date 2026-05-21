from __future__ import annotations

from PySide6.QtWidgets import QLabel, QSplitter, QVBoxLayout, QWidget

from frying_pan.gui.policy_tester.flow_input_form import FlowInputForm
from frying_pan.gui.policy_tester.match_trace_view import MatchTraceView
from frying_pan.policy.match.result import PolicyMatchResult


class PolicyTesterWorkspace(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        splitter = QSplitter()
        self.flow_input = FlowInputForm()
        self.result_label = QLabel("Matched rule: none")
        self.result_label.setWordWrap(True)
        self.trace_view = MatchTraceView()
        splitter.addWidget(self.flow_input)
        splitter.addWidget(self.result_label)
        splitter.addWidget(self.trace_view)
        layout.addWidget(splitter)

    def set_result(self, result: PolicyMatchResult) -> None:
        matched_rule = result.matched_rule.name if result.matched_rule else "none"
        self.result_label.setText(
            f"Matched rule: {matched_rule}\n"
            f"Action: {result.action}\n"
            f"Warnings: {len(result.warnings)}"
        )
        self.trace_view.set_result(result)
