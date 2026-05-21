from __future__ import annotations

from PySide6.QtWidgets import QLabel, QSplitter, QVBoxLayout, QWidget

from frying_pan.gui.modify.modify_plan_view import ModifyPlanView
from frying_pan.gui.placeholders import PlaceholderView
from frying_pan.workflows.modify.modify_plan import ModificationPlan


class ModifyWorkspace(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        splitter = QSplitter()
        self.summary_label = QLabel("Modify Plan: no staged plan loaded")
        self.summary_label.setWordWrap(True)
        splitter.addWidget(self.summary_label)
        splitter.addWidget(
            PlaceholderView("Details", "Selected object or rule details placeholder.")
        )
        self.plan_view = ModifyPlanView()
        splitter.addWidget(self.plan_view)
        layout.addWidget(splitter)

    def set_plan(self, plan: ModificationPlan) -> None:
        self.summary_label.setText(
            f"Status: {plan.status.value}\n"
            f"Actions: {plan.action_count}\n"
            f"Validation messages: {len(plan.validation.messages)}"
        )
        self.plan_view.set_plan(plan)
