from __future__ import annotations

from PySide6.QtWidgets import QSplitter, QVBoxLayout, QWidget

from frying_pan.gui.modify.modify_plan_view import ModifyPlanView
from frying_pan.gui.placeholders import PlaceholderView


class ModifyWorkspace(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        splitter = QSplitter()
        splitter.addWidget(
            PlaceholderView("Config Tree", "Single-config inventory tree placeholder.")
        )
        splitter.addWidget(
            PlaceholderView("Details", "Selected object or rule details placeholder.")
        )
        splitter.addWidget(ModifyPlanView())
        layout.addWidget(splitter)
