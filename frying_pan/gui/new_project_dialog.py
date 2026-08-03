from __future__ import annotations

import re
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from frying_pan.storage.workspace import MANIFEST_NAME

_WINDOWS_INVALID_CHARACTERS = re.compile(r'[<>:"/\\|?*]')
_WINDOWS_RESERVED_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{number}" for number in range(1, 10)),
    *(f"LPT{number}" for number in range(1, 10)),
}


class NewProjectDialog(QDialog):
    """Collect the project name and parent directory as one atomic choice."""

    def __init__(self, start_directory: Path, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Create New Frying-PAN Project")
        self.setModal(True)
        self.setMinimumWidth(620)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 18)
        layout.setSpacing(14)

        title = QLabel("Create a new project")
        title.setObjectName("CardHeading")
        description = QLabel(
            "Choose a project name and where it should be stored. Frying-PAN will create "
            "a portable project folder containing sources, cache, exports, and logs."
        )
        description.setProperty("muted", True)
        description.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(description)

        form = QFormLayout()
        form.setContentsMargins(0, 4, 0, 0)
        form.setHorizontalSpacing(14)
        form.setVerticalSpacing(12)

        self.name_edit = QLineEdit()
        self.name_edit.setObjectName("ProjectNameEdit")
        self.name_edit.setPlaceholderText("Example: Branch Firewall Migration")
        self.name_edit.setClearButtonEnabled(True)
        form.addRow("Project name", self.name_edit)

        location_row = QHBoxLayout()
        location_row.setSpacing(7)
        self.location_edit = QLineEdit(str(start_directory))
        self.location_edit.setObjectName("ProjectLocationEdit")
        self.location_edit.setClearButtonEnabled(True)
        self.browse_button = QPushButton("Browse…")
        location_row.addWidget(self.location_edit, 1)
        location_row.addWidget(self.browse_button)
        form.addRow("Parent directory", location_row)
        layout.addLayout(form)

        preview_heading = QLabel("Project folder")
        preview_heading.setProperty("muted", True)
        self.path_preview = QLabel()
        self.path_preview.setObjectName("ProjectPathPreview")
        self.path_preview.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.path_preview.setWordWrap(True)
        layout.addWidget(preview_heading)
        layout.addWidget(self.path_preview)

        self.validation_label = QLabel()
        self.validation_label.setObjectName("ValidationMessage")
        self.validation_label.setWordWrap(True)
        layout.addWidget(self.validation_label)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.create_button = self.buttons.button(QDialogButtonBox.StandardButton.Ok)
        self.create_button.setText("Create Project")
        self.create_button.setProperty("primary", True)
        layout.addWidget(self.buttons)

        self.name_edit.textChanged.connect(self._refresh)
        self.location_edit.textChanged.connect(self._refresh)
        self.browse_button.clicked.connect(self._browse)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        self._refresh()
        self.name_edit.setFocus()

    def project_name(self) -> str:
        return self.name_edit.text().strip()

    def parent_directory(self) -> Path:
        return Path(self.location_edit.text().strip()).expanduser()

    def project_root(self) -> Path:
        return self.parent_directory() / self.project_name()

    def _browse(self) -> None:
        selected = QFileDialog.getExistingDirectory(
            self,
            "Choose Parent Directory",
            str(self.parent_directory()),
            QFileDialog.Option.ShowDirsOnly,
        )
        if selected:
            self.location_edit.setText(selected)

    def _refresh(self) -> None:
        name = self.project_name()
        location_text = self.location_edit.text().strip()
        preview = Path(location_text).expanduser() / name if location_text else Path(name)
        self.path_preview.setText(str(preview) if name or location_text else "—")

        error = self._validation_error()
        self.validation_label.setText(error or "A new portable workspace will be created here.")
        self.validation_label.setProperty("valid", not bool(error))
        self.validation_label.style().unpolish(self.validation_label)
        self.validation_label.style().polish(self.validation_label)
        self.create_button.setEnabled(not bool(error))

    def _validation_error(self) -> str | None:
        name = self.project_name()
        if not name:
            return "Enter a project name."
        if name in {".", ".."}:
            return "Choose a project name other than '.' or '..'."
        if _WINDOWS_INVALID_CHARACTERS.search(name):
            return 'Project names cannot contain < > : " / \\ | ? *.'
        if name.endswith((".", " ")):
            return "Project names cannot end with a period or space on Windows."
        if name.split(".", maxsplit=1)[0].upper() in _WINDOWS_RESERVED_NAMES:
            return f"{name!r} is a reserved Windows name."

        location_text = self.location_edit.text().strip()
        if not location_text:
            return "Choose a parent directory."
        parent = self.parent_directory()
        if not parent.exists():
            return "The parent directory does not exist."
        if not parent.is_dir():
            return "The selected location is not a directory."

        root = self.project_root()
        if root.exists() and not root.is_dir():
            return "A file already exists at the project folder path."
        if (root / MANIFEST_NAME).exists():
            return "A Frying-PAN project already exists at this location."
        if root.is_dir():
            try:
                if any(root.iterdir()):
                    return "The project folder already exists and is not empty."
            except OSError:
                return "The project folder cannot be inspected."
        return None
