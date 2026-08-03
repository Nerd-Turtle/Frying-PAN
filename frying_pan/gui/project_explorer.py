from __future__ import annotations

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QSizePolicy,
    QStyle,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from frying_pan.storage.workspace import ProjectWorkspace


class ProjectExplorer(QWidget):
    """Project-local navigation kept separate from workflow navigation."""

    new_project_requested = Signal()
    open_project_requested = Signal()
    import_source_requested = Signal()
    export_xml_requested = Signal()
    source_activated = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._workspace: ProjectWorkspace | None = None
        self.setObjectName("ProjectExplorer")
        self.setMinimumWidth(220)
        self.setMaximumWidth(380)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        heading_row = QHBoxLayout()
        heading = QLabel("PROJECT EXPLORER")
        heading.setObjectName("SidebarHeading")
        heading_row.addWidget(heading)
        heading_row.addStretch()
        layout.addLayout(heading_row)

        self.project_label = QLabel("NO PROJECT OPEN")
        self.project_label.setObjectName("ProjectHeading")
        self.project_label.setWordWrap(True)
        layout.addWidget(self.project_label)

        project_action_row = QHBoxLayout()
        project_action_row.setSpacing(6)
        self.new_button = QPushButton("New Project")
        self.open_button = QPushButton("Open Project")
        for button in (self.new_button, self.open_button):
            button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            project_action_row.addWidget(button)
        layout.addLayout(project_action_row)

        xml_action_row = QHBoxLayout()
        xml_action_row.setSpacing(6)
        self.import_button = QPushButton("Import XML")
        self.export_button = QPushButton("Export XML")
        self.import_button.setEnabled(False)
        self.export_button.setEnabled(False)
        for button in (self.import_button, self.export_button):
            button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            xml_action_row.addWidget(button)
        layout.addLayout(xml_action_row)

        self.tree = QTreeWidget()
        self.tree.setObjectName("ProjectTree")
        self.tree.setHeaderHidden(True)
        self.tree.setIndentation(16)
        self.tree.setUniformRowHeights(True)
        self.tree.setAnimated(True)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        layout.addWidget(self.tree, 1)

        self.empty_label = QLabel(
            "Create or open a portable project workspace to begin.\n\n"
            "Configuration files remain on this computer."
        )
        self.empty_label.setObjectName("MutedCopy")
        self.empty_label.setWordWrap(True)
        layout.addWidget(self.empty_label)

        self.new_button.clicked.connect(self.new_project_requested)
        self.open_button.clicked.connect(self.open_project_requested)
        self.import_button.clicked.connect(self.import_source_requested)
        self.export_button.clicked.connect(self.export_xml_requested)
        self.tree.itemClicked.connect(self._activate_item)
        self.tree.customContextMenuRequested.connect(self._show_context_menu)

    def set_workspace(self, workspace: ProjectWorkspace | None) -> None:
        self._workspace = workspace
        self.tree.clear()
        self.import_button.setEnabled(workspace is not None)
        self.export_button.setEnabled(bool(workspace and workspace.manifest.sources))
        self.empty_label.setVisible(workspace is None)
        if workspace is None:
            self.project_label.setText("NO PROJECT OPEN")
            return

        self.project_label.setText(workspace.manifest.name.upper())
        style = self.style()
        project_item = QTreeWidgetItem([workspace.manifest.name])
        project_item.setData(0, Qt.ItemDataRole.UserRole + 1, "project")
        project_item.setIcon(0, style.standardIcon(QStyle.StandardPixmap.SP_DirHomeIcon))
        project_item.setToolTip(0, str(workspace.root))

        sources_item = QTreeWidgetItem([f"XML Files ({len(workspace.manifest.sources)})"])
        sources_item.setData(0, Qt.ItemDataRole.UserRole + 1, "sources")
        sources_item.setIcon(0, style.standardIcon(QStyle.StandardPixmap.SP_DirIcon))
        project_item.addChild(sources_item)
        for source in workspace.manifest.sources:
            source_item = QTreeWidgetItem([source.display_name])
            source_item.setData(0, Qt.ItemDataRole.UserRole, source.id)
            source_item.setData(0, Qt.ItemDataRole.UserRole + 1, "source")
            source_item.setIcon(0, style.standardIcon(QStyle.StandardPixmap.SP_FileIcon))
            source_item.setToolTip(
                0,
                f"{source.source_type.value}\n{source.workspace_path or source.original_path}",
            )
            sources_item.addChild(source_item)

        reports_item = QTreeWidgetItem(["Exports"])
        reports_item.setData(0, Qt.ItemDataRole.UserRole + 1, "exports")
        reports_item.setIcon(0, style.standardIcon(QStyle.StandardPixmap.SP_DirIcon))
        reports_item.setToolTip(0, str(workspace.exports_dir))
        project_item.addChild(reports_item)

        self.tree.addTopLevelItem(project_item)
        project_item.setExpanded(True)
        sources_item.setExpanded(True)

    def select_source(self, source_id: str) -> None:
        iterator = self.tree.invisibleRootItem()
        for root_index in range(iterator.childCount()):
            match = self._find_source_item(iterator.child(root_index), source_id)
            if match is not None:
                self.tree.setCurrentItem(match)
                return

    def _find_source_item(
        self, item: QTreeWidgetItem, source_id: str
    ) -> QTreeWidgetItem | None:
        if item.data(0, Qt.ItemDataRole.UserRole) == source_id:
            return item
        for index in range(item.childCount()):
            match = self._find_source_item(item.child(index), source_id)
            if match is not None:
                return match
        return None

    def _activate_item(self, item: QTreeWidgetItem) -> None:
        source_id = item.data(0, Qt.ItemDataRole.UserRole)
        if source_id:
            self.source_activated.emit(str(source_id))

    def build_context_menu(self, item: QTreeWidgetItem | None) -> QMenu:
        menu = QMenu(self)
        kind = item.data(0, Qt.ItemDataRole.UserRole + 1) if item else None

        if kind in {None, "project"}:
            new_action = menu.addAction("New Project…")
            open_action = menu.addAction("Open Project…")
            new_action.triggered.connect(lambda: self.new_project_requested.emit())
            open_action.triggered.connect(lambda: self.open_project_requested.emit())

        if kind == "source":
            source_id = item.data(0, Qt.ItemDataRole.UserRole)
            activate_action = menu.addAction("Open in Inventory")
            activate_action.triggered.connect(
                lambda: self.source_activated.emit(str(source_id))
            )

        if kind in {"project", "sources", "source", "exports"}:
            if menu.actions():
                menu.addSeparator()
            import_action = menu.addAction("Import XML…")
            export_action = menu.addAction("Export XML…")
            import_action.setEnabled(self._workspace is not None)
            export_action.setEnabled(
                bool(self._workspace and self._workspace.manifest.sources)
            )
            import_action.triggered.connect(lambda: self.import_source_requested.emit())
            export_action.triggered.connect(lambda: self.export_xml_requested.emit())

        return menu

    def _show_context_menu(self, position: QPoint) -> None:
        menu = self.build_context_menu(self.tree.itemAt(position))
        if menu.actions():
            menu.exec(self.tree.viewport().mapToGlobal(position))
