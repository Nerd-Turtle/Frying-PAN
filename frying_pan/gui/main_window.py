from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QListWidget, QListWidgetItem, QMainWindow, QSplitter, QStackedWidget

from frying_pan.gui.convert.conversion_workspace import ConversionWorkspace
from frying_pan.gui.dashboard.dashboard_view import DashboardView
from frying_pan.gui.dedupe.dedupe_workspace import DedupeWorkspace
from frying_pan.gui.inventory.inventory_view import InventoryView
from frying_pan.gui.migrate.migration_workspace import MigrationWorkspace
from frying_pan.gui.modify.modify_workspace import ModifyWorkspace
from frying_pan.gui.placeholders import PlaceholderView
from frying_pan.gui.policy_audit.audit_workspace import AuditWorkspace
from frying_pan.gui.policy_tester.tester_workspace import PolicyTesterWorkspace
from frying_pan.gui.reports.report_view import ReportView
from frying_pan.gui.sources.source_import_view import SourceImportView


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Frying-PAN")

        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.navigation = QListWidget()
        self.navigation.setFixedWidth(220)
        self.stack = QStackedWidget()
        splitter.addWidget(self.navigation)
        splitter.addWidget(self.stack)
        splitter.setStretchFactor(1, 1)
        self.setCentralWidget(splitter)

        self._add_page("Dashboard", DashboardView())
        self._add_page("Sources", SourceImportView())
        self._add_page("Inventory", InventoryView())
        self._add_page("Modify", ModifyWorkspace())
        self._add_page("Migrate", MigrationWorkspace())
        self._add_page("Convert", ConversionWorkspace())
        self._add_page("Policy Audit", AuditWorkspace())
        self._add_page("Policy Tester", PolicyTesterWorkspace())
        self._add_page("Dedupe / Conflicts", DedupeWorkspace())
        self._add_page("Reports", ReportView())
        self._add_page(
            "Settings",
            PlaceholderView(
                "Settings",
                "Local application preferences will live here. "
                "No hosted account settings are planned.",
            ),
        )

        self.navigation.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.navigation.setCurrentRow(0)

    def _add_page(self, name: str, widget) -> None:
        self.navigation.addItem(QListWidgetItem(name))
        self.stack.addWidget(widget)
