from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from frying_pan.storage.workspace import ProjectWorkspace


class SourceImportView(QWidget):
    import_requested = Signal()
    export_xml_requested = Signal()
    source_activated = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)

        heading_row = QHBoxLayout()
        heading_copy = QVBoxLayout()
        title = QLabel("Explorer")
        title.setObjectName("PageTitle")
        subtitle = QLabel(
            "Manage the active project and its local Panorama or firewall XML files."
        )
        subtitle.setObjectName("PageSubtitle")
        subtitle.setWordWrap(True)
        heading_copy.addWidget(title)
        heading_copy.addWidget(subtitle)
        heading_row.addLayout(heading_copy, 1)
        self.import_button = QPushButton("Import XML")
        self.import_button.setProperty("primary", True)
        self.import_button.setEnabled(False)
        self.export_button = QPushButton("Export XML")
        self.export_button.setEnabled(False)
        heading_row.addWidget(self.import_button)
        heading_row.addWidget(self.export_button)
        layout.addLayout(heading_row)

        self.workspace_label = QLabel("No project open")
        self.workspace_label.setProperty("muted", True)
        layout.addWidget(self.workspace_label)

        self.sources_table = QTableWidget(0, 4)
        self.sources_table.setHorizontalHeaderLabels(
            ["XML file", "Detected type", "Imported", "Project copy"]
        )
        self.sources_table.setAlternatingRowColors(True)
        self.sources_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.sources_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.sources_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.sources_table.verticalHeader().setVisible(False)
        header = self.sources_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.sources_table, 1)

        self.empty_label = QLabel(
            "No XML files have been imported. The original file is never modified."
        )
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setProperty("muted", True)
        layout.addWidget(self.empty_label)

        self.import_button.clicked.connect(self.import_requested)
        self.export_button.clicked.connect(self.export_xml_requested)
        self.sources_table.cellDoubleClicked.connect(self._activate_row)

    def set_workspace(self, workspace: ProjectWorkspace | None) -> None:
        self.sources_table.setRowCount(0)
        self.import_button.setEnabled(workspace is not None)
        self.export_button.setEnabled(bool(workspace and workspace.manifest.sources))
        if workspace is None:
            self.workspace_label.setText("No project open")
            self.empty_label.setVisible(True)
            return

        self.workspace_label.setText(str(workspace.root))
        for source in workspace.manifest.sources:
            row = self.sources_table.rowCount()
            self.sources_table.insertRow(row)
            imported = source.imported_at.astimezone().strftime("%Y-%m-%d %H:%M")
            location = str(source.workspace_path or source.original_path)
            values = (source.display_name, source.source_type.value, imported, location)
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.ItemDataRole.UserRole, source.id)
                item.setToolTip(location)
                self.sources_table.setItem(row, column, item)
        self.empty_label.setVisible(not workspace.manifest.sources)

    def select_source(self, source_id: str) -> None:
        for row in range(self.sources_table.rowCount()):
            item = self.sources_table.item(row, 0)
            if item and item.data(Qt.ItemDataRole.UserRole) == source_id:
                self.sources_table.selectRow(row)
                return

    def _activate_row(self, row: int) -> None:
        item = self.sources_table.item(row, 0)
        if item is not None:
            self.source_activated.emit(str(item.data(Qt.ItemDataRole.UserRole)))
