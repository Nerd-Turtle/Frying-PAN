from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from frying_pan.gui.convert.conversion_workspace import ConversionWorkspace
from frying_pan.workflows.convert.conversion_workflow import ConversionWorkflow

FIXTURES = Path(__file__).parent / "fixtures"


def _app() -> QApplication:
    app = QApplication.instance()
    return app if app is not None else QApplication([])


def test_convert_workspace_displays_package_counts_and_warnings() -> None:
    _app()
    package = ConversionWorkflow().convert_generic_json(
        FIXTURES / "vendor_future" / "generic_import.json"
    )
    workspace = ConversionWorkspace()

    workspace.set_package(package)

    assert "Generic Conversion Fixture" in workspace.source_view.status_label.text()
    assert "Security rules: 1" in workspace.preview_label.text()
    assert workspace.mapping_view.table.rowCount() == (
        len(package.warnings) + len(package.unsupported_features)
    )
