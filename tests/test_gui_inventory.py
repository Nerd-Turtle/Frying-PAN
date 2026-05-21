from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from frying_pan.gui.inventory.inventory_view import InventoryView
from frying_pan.gui.main_window import MainWindow
from frying_pan.gui.sources.source_tree_model import build_source_tree_model
from frying_pan.sources.base import SourceConfig, SourceType
from frying_pan.sources.panorama_xml import PanoramaXmlAdapter

FIXTURES = Path(__file__).parent / "fixtures"


def _app() -> QApplication:
    app = QApplication.instance()
    return app if app is not None else QApplication([])


def _config():
    source_path = FIXTURES / "panorama" / "reference_config_items.xml"
    source = SourceConfig(
        display_name=source_path.name,
        original_path=source_path,
        source_type=SourceType.PANORAMA_XML,
    )
    return PanoramaXmlAdapter().parse(source)


def test_inventory_view_populates_tables_offscreen() -> None:
    _app()
    config = _config()

    view = InventoryView(config)

    assert view.scopes_table.rowCount() == len(config.scopes)
    assert view.objects_table.rowCount() == len(config.entities)
    assert view.rules_table.rowCount() == len(config.security_rules)


def test_source_tree_model_includes_scopes_objects_and_rules() -> None:
    _app()
    model = build_source_tree_model(_config())

    root = model.invisibleRootItem()

    assert root.rowCount() == 3
    assert root.child(0).text() == "Scopes"
    assert root.child(1).text() == "Objects"
    assert root.child(2).text() == "Security Rules"


def test_main_window_constructs_inventory_page_offscreen() -> None:
    _app()
    window = MainWindow()

    nav_items = [window.navigation.item(row).text() for row in range(window.navigation.count())]

    assert "Inventory" in nav_items
