from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from frying_pan.analysis.dedupe import DedupeAnalysisEngine
from frying_pan.gui.dedupe.dedupe_workspace import DedupeWorkspace
from frying_pan.gui.main_window import MainWindow
from frying_pan.normalized.addresses import AddressKind, AddressObject
from frying_pan.normalized.config import NormalizedConfig
from frying_pan.sources.base import SourceType


def _app() -> QApplication:
    app = QApplication.instance()
    return app if app is not None else QApplication([])


def test_dedupe_workspace_displays_result_offscreen() -> None:
    _app()
    workspace = DedupeWorkspace()
    config = NormalizedConfig(
        source_id="source-1",
        source_type=SourceType.FIREWALL_XML,
        entities=[
            AddressObject(
                name="a",
                scope_path="vsys/vsys1",
                address_kind=AddressKind.IP_NETMASK,
                value="192.0.2.10",
            )
        ],
    )
    result = DedupeAnalysisEngine().analyze(config)

    workspace.set_result(result)

    assert "Findings:" in workspace.summary_label.text()
    assert workspace.findings_table.rowCount() == result.finding_count


def test_main_window_includes_dedupe_page() -> None:
    _app()
    window = MainWindow()

    nav_items = [window.navigation.item(row).text() for row in range(window.navigation.count())]

    assert "Dedupe / Conflicts" in nav_items
