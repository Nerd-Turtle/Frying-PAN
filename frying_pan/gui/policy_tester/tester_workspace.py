from __future__ import annotations

from PySide6.QtWidgets import QSplitter, QVBoxLayout, QWidget

from frying_pan.gui.placeholders import PlaceholderView
from frying_pan.gui.policy_tester.flow_input_form import FlowInputForm
from frying_pan.gui.policy_tester.match_trace_view import MatchTraceView


class PolicyTesterWorkspace(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        splitter = QSplitter()
        splitter.addWidget(FlowInputForm())
        splitter.addWidget(PlaceholderView("Matched Rule", "First matched rule and action result."))
        splitter.addWidget(MatchTraceView())
        layout.addWidget(splitter)
