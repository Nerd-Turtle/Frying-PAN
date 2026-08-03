from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSettings, QSize, Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QSizePolicy,
    QSplitter,
    QStackedWidget,
    QStyle,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from frying_pan.analysis.dedupe import DedupeAnalysisEngine
from frying_pan.export.xml_exporter import XmlExportNotReadyError, export_xml
from frying_pan.gui.convert.conversion_workspace import ConversionWorkspace
from frying_pan.gui.dedupe.dedupe_workspace import DedupeWorkspace
from frying_pan.gui.inventory.inventory_view import InventoryView
from frying_pan.gui.migrate.migration_workspace import MigrationWorkspace
from frying_pan.gui.modify.modify_workspace import ModifyWorkspace
from frying_pan.gui.new_project_dialog import NewProjectDialog
from frying_pan.gui.placeholders import PlaceholderView
from frying_pan.gui.policy_audit.audit_workspace import AuditWorkspace
from frying_pan.gui.policy_tester.tester_workspace import PolicyTesterWorkspace
from frying_pan.gui.project_explorer import ProjectExplorer
from frying_pan.gui.reports.report_view import ReportView
from frying_pan.gui.sources.source_import_view import SourceImportView
from frying_pan.normalized.config import NormalizedConfig
from frying_pan.policy.audit.audit_engine import PolicyAuditEngine
from frying_pan.policy.match.match_engine import PolicyMatchEngine
from frying_pan.sources.base import SourceConfig
from frying_pan.sources.parsing import SourceParseError, parse_source
from frying_pan.storage.workspace import ProjectWorkspace
from frying_pan.workflows.modify.modify_workflow import ModifyWorkflow


class MainWindow(QMainWindow):
    """Desktop workbench shell and thin orchestration for local project workflows."""

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("MainWindow")
        self.setWindowTitle("Frying-PAN")
        self.setMinimumSize(1000, 680)

        self.settings = QSettings()
        self.workspace: ProjectWorkspace | None = None
        self.active_source: SourceConfig | None = None
        self.active_config: NormalizedConfig | None = None
        self._configs: dict[str, NormalizedConfig] = {}
        self._page_names: list[str] = []

        self._build_actions()
        self._build_menu()
        self._build_toolbar()
        self._build_workbench()
        self._build_status_bar()
        self._connect_project_actions()
        self._set_status("Ready — create or open a local project")

    def _build_actions(self) -> None:
        style = self.style()
        self.new_project_action = QAction(
            style.standardIcon(QStyle.StandardPixmap.SP_FileDialogNewFolder),
            "New Project…",
            self,
        )
        self.new_project_action.setShortcut(QKeySequence.StandardKey.New)
        self.open_project_action = QAction(
            style.standardIcon(QStyle.StandardPixmap.SP_DialogOpenButton),
            "Open Project…",
            self,
        )
        self.open_project_action.setShortcut(QKeySequence.StandardKey.Open)
        self.import_source_action = QAction(
            style.standardIcon(QStyle.StandardPixmap.SP_FileIcon),
            "Import XML…",
            self,
        )
        self.import_source_action.setShortcut(QKeySequence("Ctrl+I"))
        self.import_source_action.setEnabled(False)
        self.export_xml_action = QAction(
            style.standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton),
            "Export XML…",
            self,
        )
        self.export_xml_action.setEnabled(False)
        self.export_xml_action.setToolTip(
            "XML export remains blocked until serializer validation is complete."
        )
        self.close_project_action = QAction("Close Project", self)
        self.close_project_action.setEnabled(False)
        self.exit_action = QAction("Exit", self)
        self.exit_action.setShortcut(QKeySequence.StandardKey.Quit)

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu("&File")
        file_menu.addAction(self.new_project_action)
        file_menu.addAction(self.open_project_action)
        file_menu.addSeparator()
        file_menu.addAction(self.import_source_action)
        file_menu.addAction(self.export_xml_action)
        file_menu.addSeparator()
        file_menu.addAction(self.close_project_action)
        file_menu.addAction(self.exit_action)

        view_menu = self.menuBar().addMenu("&View")
        self.toggle_explorer_action = QAction("Project Explorer", self)
        self.toggle_explorer_action.setCheckable(True)
        self.toggle_explorer_action.setChecked(True)
        self.toggle_explorer_action.setShortcut(QKeySequence("Ctrl+Shift+E"))
        view_menu.addAction(self.toggle_explorer_action)

        help_menu = self.menuBar().addMenu("&Help")
        about_action = QAction("About Frying-PAN", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Workbench")
        toolbar.setObjectName("WorkbenchToolbar")
        toolbar.setMovable(False)
        toolbar.setFloatable(False)
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        toolbar.addAction(self.new_project_action)
        toolbar.addAction(self.open_project_action)
        toolbar.addAction(self.import_source_action)
        toolbar.addAction(self.export_xml_action)
        toolbar.addSeparator()

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)
        self.command_center = QLineEdit()
        self.command_center.setObjectName("CommandCenter")
        self.command_center.setPlaceholderText("Search workflows (Ctrl+K)")
        self.command_center.setClearButtonEnabled(True)
        toolbar.addWidget(self.command_center)
        second_spacer = QWidget()
        second_spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(second_spacer)
        self.addToolBar(toolbar)

        focus_search = QAction(self)
        focus_search.setShortcut(QKeySequence("Ctrl+K"))
        focus_search.triggered.connect(self.command_center.setFocus)
        self.addAction(focus_search)
        self.command_center.textChanged.connect(self._filter_navigation)
        self.command_center.returnPressed.connect(self._open_first_visible_page)

    def _build_workbench(self) -> None:
        root = QWidget()
        root.setObjectName("WorkbenchRoot")
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.workbench_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.workbench_splitter.setChildrenCollapsible(False)
        root_layout.addWidget(self.workbench_splitter)

        self.navigation = QListWidget()
        self.navigation.setObjectName("ActivityNavigation")
        self.navigation.setFixedWidth(178)
        self.navigation.setIconSize(QSize(18, 18))
        self.navigation.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.workbench_splitter.addWidget(self.navigation)

        self.explorer = ProjectExplorer()
        self.workbench_splitter.addWidget(self.explorer)

        editor = QWidget()
        editor_layout = QVBoxLayout(editor)
        editor_layout.setContentsMargins(0, 0, 0, 0)
        editor_layout.setSpacing(0)
        self.stack = QStackedWidget()
        self.stack.setObjectName("WorkbenchStack")
        editor_layout.addWidget(self.stack, 1)
        self.workbench_splitter.addWidget(editor)
        self.workbench_splitter.setStretchFactor(2, 1)
        self.workbench_splitter.setSizes([178, 270, 900])
        self.setCentralWidget(root)

        self.sources_view = SourceImportView()
        self.inventory_view = InventoryView()
        self.modify_view = ModifyWorkspace()
        self.migrate_view = MigrationWorkspace()
        self.convert_view = ConversionWorkspace()
        self.audit_view = AuditWorkspace()
        self.policy_tester_view = PolicyTesterWorkspace()
        self.dedupe_view = DedupeWorkspace()
        self.reports_view = ReportView()
        self.settings_view = PlaceholderView(
            "Settings",
            "Local application preferences will live here. No hosted account settings are "
            "planned.",
        )

        self._add_page("Explorer", self.sources_view, QStyle.StandardPixmap.SP_DirIcon)
        self._add_page(
            "Inventory", self.inventory_view, QStyle.StandardPixmap.SP_FileDialogDetailedView
        )
        self._add_page("Modify", self.modify_view, QStyle.StandardPixmap.SP_FileDialogContentsView)
        self._add_page("Migrate", self.migrate_view, QStyle.StandardPixmap.SP_ArrowForward)
        self._add_page("Convert", self.convert_view, QStyle.StandardPixmap.SP_BrowserReload)
        self._add_page("Policy Audit", self.audit_view, QStyle.StandardPixmap.SP_MessageBoxWarning)
        self._add_page(
            "Policy Tester", self.policy_tester_view, QStyle.StandardPixmap.SP_DialogApplyButton
        )
        self._add_page(
            "Dedupe / Conflicts", self.dedupe_view, QStyle.StandardPixmap.SP_FileDialogListView
        )
        self._add_page("Reports", self.reports_view, QStyle.StandardPixmap.SP_FileIcon)
        self._add_page("Settings", self.settings_view, QStyle.StandardPixmap.SP_FileDialogInfoView)

        self.navigation.currentRowChanged.connect(self._navigation_changed)
        self.navigation.setCurrentRow(0)

    def _build_status_bar(self) -> None:
        self.status_message = QLabel()
        self.project_status = QLabel("No project")
        self.source_status = QLabel("No XML")
        self.statusBar().addWidget(self.status_message, 1)
        self.statusBar().addPermanentWidget(self.project_status)
        self.statusBar().addPermanentWidget(self.source_status)

    def _connect_project_actions(self) -> None:
        self.new_project_action.triggered.connect(self._new_project_dialog)
        self.open_project_action.triggered.connect(self._open_project_dialog)
        self.import_source_action.triggered.connect(self._import_source_dialog)
        self.export_xml_action.triggered.connect(self._export_xml)
        self.close_project_action.triggered.connect(self.close_project)
        self.exit_action.triggered.connect(self.close)
        self.toggle_explorer_action.toggled.connect(self.explorer.setVisible)

        self.explorer.new_project_requested.connect(self._new_project_dialog)
        self.explorer.open_project_requested.connect(self._open_project_dialog)
        self.explorer.import_source_requested.connect(self._import_source_dialog)
        self.explorer.export_xml_requested.connect(self._export_xml)
        self.explorer.source_activated.connect(self.activate_source)
        self.sources_view.import_requested.connect(self._import_source_dialog)
        self.sources_view.export_xml_requested.connect(self._export_xml)
        self.sources_view.source_activated.connect(self.activate_source)
        self.policy_tester_view.run_requested.connect(self._run_policy_test)

    def _add_page(
        self, name: str, widget: QWidget, icon_type: QStyle.StandardPixmap
    ) -> None:
        icon = self.style().standardIcon(icon_type)
        item = QListWidgetItem(icon, name)
        item.setToolTip(name)
        self.navigation.addItem(item)
        self.stack.addWidget(widget)
        self._page_names.append(name)

    def load_workspace(self, workspace_or_root: ProjectWorkspace | Path) -> ProjectWorkspace:
        workspace = (
            workspace_or_root
            if isinstance(workspace_or_root, ProjectWorkspace)
            else ProjectWorkspace.open(Path(workspace_or_root))
        )
        self.workspace = workspace
        self.active_source = None
        self.active_config = None
        self._configs.clear()
        self.sources_view.set_workspace(workspace)
        self.explorer.set_workspace(workspace)
        self.import_source_action.setEnabled(True)
        self.export_xml_action.setEnabled(bool(workspace.manifest.sources))
        self.close_project_action.setEnabled(True)
        self.project_status.setText(workspace.manifest.name)
        self.source_status.setText("No XML")
        self.setWindowTitle(f"{workspace.manifest.name} — Frying-PAN")
        self.settings.setValue("recent/project", str(workspace.root))
        self.settings.setValue("recent/directory", str(workspace.root.parent))
        self._set_status(f"Opened project: {workspace.root}")
        self.show_page("Explorer")
        return workspace

    def import_source_path(self, source_path: Path) -> SourceConfig:
        if self.workspace is None:
            raise RuntimeError("Create or open a project before importing a source.")
        source_path = Path(source_path)
        if not source_path.is_file():
            raise FileNotFoundError(source_path)

        source = self.workspace.import_source(source_path)
        self.sources_view.set_workspace(self.workspace)
        self.explorer.set_workspace(self.workspace)
        self.export_xml_action.setEnabled(True)
        self.settings.setValue("recent/source_directory", str(source_path.parent))
        config = self._parse_source(source)
        if config is None:
            self.show_page("Explorer")
        else:
            self._activate_parsed_source(source, config)
            self.show_page("Inventory")
        return source

    def activate_source(self, source_id: str) -> None:
        if self.workspace is None:
            return
        source = next(
            (item for item in self.workspace.manifest.sources if item.id == source_id), None
        )
        if source is None:
            self._set_status(f"Source is no longer present in the project: {source_id}")
            return
        config = self._configs.get(source.id) or self._parse_source(source)
        if config is None:
            self.show_page("Explorer")
            return
        self._activate_parsed_source(source, config)
        self.show_page("Inventory")

    def close_project(self) -> None:
        self.workspace = None
        self.active_source = None
        self.active_config = None
        self._configs.clear()
        self.sources_view.set_workspace(None)
        self.explorer.set_workspace(None)
        self.import_source_action.setEnabled(False)
        self.export_xml_action.setEnabled(False)
        self.close_project_action.setEnabled(False)
        self.project_status.setText("No project")
        self.source_status.setText("No XML")
        self.setWindowTitle("Frying-PAN")
        self._set_status("Project closed")
        self.show_page("Explorer")

    def show_page(self, name: str) -> None:
        try:
            row = self._page_names.index(name)
        except ValueError:
            return
        self.navigation.setCurrentRow(row)

    def _parse_source(self, source: SourceConfig) -> NormalizedConfig | None:
        path = source.workspace_path or source.original_path
        self._set_status(f"Parsing {source.display_name}…")
        try:
            config = parse_source(path)
        except (OSError, SourceParseError, ValueError) as exc:
            self._set_status(f"Imported {source.display_name}, but parsing is unavailable: {exc}")
            return None
        config = config.model_copy(update={"source_id": source.id})
        self._configs[source.id] = config
        return config

    def _activate_parsed_source(
        self, source: SourceConfig, config: NormalizedConfig
    ) -> None:
        self.active_source = source
        self.active_config = config
        self.inventory_view.set_config(config)
        self.audit_view.set_result(PolicyAuditEngine().audit_config(config))
        self.dedupe_view.set_result(DedupeAnalysisEngine().analyze(config))
        workflow = ModifyWorkflow()
        plan = workflow.create_plan_from_config(config)
        workflow.validate_plan(config, plan)
        self.modify_view.set_plan(plan)
        self.policy_tester_view.set_config(config, source.display_name)
        self.sources_view.select_source(source.id)
        self.explorer.select_source(source.id)
        self.source_status.setText(source.display_name)
        self._set_status(
            f"Loaded {source.display_name}: {len(config.entities)} objects, "
            f"{len(config.security_rules)} security rules"
        )

    def _run_policy_test(self) -> None:
        if self.active_config is None:
            self._set_status("Load a supported configuration before running Policy Tester")
            return
        try:
            test_case = self.policy_tester_view.flow_input.to_test_case()
            result = PolicyMatchEngine().evaluate_config(
                self.active_config,
                test_case,
                self.policy_tester_view.selected_scope(),
            )
        except ValueError as exc:
            QMessageBox.warning(self, "Invalid test flow", str(exc))
            self._set_status(f"Policy test input error: {exc}")
            return
        self.policy_tester_view.set_result(result)
        matched = result.matched_rule.name if result.matched_rule else "no matching rule"
        self._set_status(f"Policy test complete: {matched}")

    def _new_project_dialog(self) -> None:
        start_directory = Path(
            self.settings.value("recent/directory", str(Path.home()), type=str)
        )
        dialog = NewProjectDialog(start_directory, self)
        if not dialog.exec():
            return
        try:
            workspace = ProjectWorkspace.create(
                dialog.project_root(), dialog.project_name()
            )
            self.load_workspace(workspace)
        except (OSError, ValueError) as exc:
            self._show_error("Could not create project", exc)

    def _open_project_dialog(self) -> None:
        start = str(
            self.settings.value("recent/project", str(Path.home()), type=str)
        )
        selected = QFileDialog.getExistingDirectory(
            self,
            "Open Frying-PAN Project",
            start,
            QFileDialog.Option.ShowDirsOnly,
        )
        if selected:
            self._try_load_workspace(Path(selected))

    def _try_load_workspace(self, root: Path) -> None:
        try:
            self.load_workspace(root)
        except (OSError, ValueError, KeyError) as exc:
            self._show_error(
                "Could not open project",
                f"{root} is not a valid Frying-PAN workspace.\n\n{exc}",
            )

    def _import_source_dialog(self) -> None:
        if self.workspace is None:
            QMessageBox.information(
                self,
                "Open a project first",
                "Create or open a local project before importing XML.",
            )
            return
        start = str(
            self.settings.value(
                "recent/source_directory", str(self.workspace.root), type=str
            )
        )
        selected, _ = QFileDialog.getOpenFileName(
            self,
            "Import XML Configuration",
            start,
            "PAN-OS XML (*.xml *.pan *.conf);;XML files (*.xml);;All files (*.*)",
        )
        if not selected:
            return
        try:
            self.import_source_path(Path(selected))
        except (OSError, RuntimeError, ValueError) as exc:
            self._show_error("Could not import XML", exc)

    def _export_xml(self) -> None:
        if self.workspace is None or not self.workspace.manifest.sources:
            QMessageBox.information(
                self,
                "No XML to export",
                "Import an XML configuration before starting an export.",
            )
            return
        try:
            export_xml()
        except XmlExportNotReadyError as exc:
            QMessageBox.information(
                self,
                "XML export is not ready",
                f"{exc}\n\nThe imported source remains unchanged.",
            )
            self._set_status("XML export remains blocked pending serializer validation")

    def _navigation_changed(self, row: int) -> None:
        if row < 0:
            return
        self.stack.setCurrentIndex(row)

    def _filter_navigation(self, text: str) -> None:
        query = text.strip().casefold()
        for row, name in enumerate(self._page_names):
            self.navigation.item(row).setHidden(bool(query) and query not in name.casefold())

    def _open_first_visible_page(self) -> None:
        for row in range(self.navigation.count()):
            if not self.navigation.item(row).isHidden():
                self.navigation.setCurrentRow(row)
                self.command_center.clear()
                return

    def _set_status(self, message: str) -> None:
        self.status_message.setText(message)

    def _show_error(self, title: str, error: object) -> None:
        self._set_status(f"{title}: {error}")
        QMessageBox.critical(self, title, str(error))

    def _show_about(self) -> None:
        QMessageBox.about(
            self,
            "About Frying-PAN",
            "Frying-PAN is an offline desktop workbench for Panorama and PAN-OS "
            "configuration analysis and change planning.",
        )
