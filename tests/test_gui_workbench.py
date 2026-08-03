from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from frying_pan.gui.main_window import MainWindow
from frying_pan.gui.new_project_dialog import NewProjectDialog
from frying_pan.storage.workspace import ProjectWorkspace

FIXTURES = Path(__file__).parent / "fixtures"


def _app() -> QApplication:
    app = QApplication.instance()
    return app if app is not None else QApplication([])


def test_workbench_shell_exposes_ide_navigation_and_project_actions() -> None:
    _app()
    window = MainWindow()

    assert window.navigation.count() == window.stack.count()
    assert window.explorer.isVisibleTo(window)
    assert not window.import_source_action.isEnabled()
    assert "create or open" in window.status_message.text().lower()
    nav_items = [
        window.navigation.item(row).text() for row in range(window.navigation.count())
    ]
    assert nav_items[0] == "Explorer"
    assert "Dashboard" not in nav_items
    assert window.new_project_action.text().startswith("New Project")
    assert window.open_project_action.text().startswith("Open Project")
    assert window.import_source_action.text().startswith("Import XML")
    assert window.export_xml_action.text().startswith("Export XML")


def test_left_navigation_displays_only_selected_workspace() -> None:
    _app()
    window = MainWindow()

    window.show_page("Explorer")

    assert window.navigation.currentItem().text() == "Explorer"
    assert window.stack.currentWidget() is window.sources_view
    assert window.stack.currentWidget() is not window.inventory_view


def test_new_project_dialog_keeps_name_and_directory_in_one_flow(tmp_path: Path) -> None:
    _app()
    dialog = NewProjectDialog(tmp_path)

    assert not dialog.create_button.isEnabled()

    dialog.name_edit.setText("Branch Firewall Migration")

    assert dialog.create_button.isEnabled()
    assert dialog.project_name() == "Branch Firewall Migration"
    assert dialog.parent_directory() == tmp_path
    assert dialog.project_root() == tmp_path / "Branch Firewall Migration"
    assert dialog.path_preview.text() == str(tmp_path / "Branch Firewall Migration")


def test_new_project_dialog_rejects_unsafe_or_occupied_windows_paths(
    tmp_path: Path,
) -> None:
    _app()
    dialog = NewProjectDialog(tmp_path)

    dialog.name_edit.setText("CON")
    assert not dialog.create_button.isEnabled()
    assert "reserved Windows name" in dialog.validation_label.text()

    occupied = tmp_path / "Existing Project"
    occupied.mkdir()
    (occupied / "notes.txt").write_text("already used", encoding="utf-8")
    dialog.name_edit.setText("Existing Project")

    assert not dialog.create_button.isEnabled()
    assert "not empty" in dialog.validation_label.text()


def test_main_window_creates_name_mapped_project_from_single_dialog(
    tmp_path: Path, monkeypatch
) -> None:
    _app()
    expected_root = tmp_path / "Seamless Project"

    class AcceptedProjectDialog:
        def __init__(self, start_directory: Path, parent: MainWindow) -> None:
            assert parent is window

        def exec(self) -> int:
            return 1

        def project_root(self) -> Path:
            return expected_root

        def project_name(self) -> str:
            return "Seamless Project"

    window = MainWindow()
    monkeypatch.setattr(
        "frying_pan.gui.main_window.NewProjectDialog", AcceptedProjectDialog
    )

    window._new_project_dialog()

    assert window.workspace is not None
    assert window.workspace.root == expected_root
    assert window.workspace.manifest.name == "Seamless Project"


def test_project_import_with_windows_safe_path_updates_workbench(tmp_path: Path) -> None:
    _app()
    workspace = ProjectWorkspace.create(tmp_path / "Project With Spaces", "Lab Project")
    window = MainWindow()
    window.load_workspace(workspace)

    source = window.import_source_path(
        FIXTURES / "firewall" / "reference_config_items_virtual_router.xml"
    )

    assert source.workspace_path is not None
    assert source.workspace_path.exists()
    assert window.workspace is not None
    assert len(window.workspace.manifest.sources) == 1
    assert window.active_source == source
    assert window.active_config is not None
    assert window.inventory_view.objects_table.rowCount() == len(window.active_config.entities)
    assert window.inventory_view.rules_table.rowCount() == len(
        window.active_config.security_rules
    )
    assert window.audit_view.findings_table.rowCount() > 0
    assert window.policy_tester_view.run_button.isEnabled()
    assert window.stack.currentWidget() is window.inventory_view
    assert window.project_status.text() == "Lab Project"
    assert window.source_status.text() == source.display_name


def test_existing_project_can_be_reopened_from_disk(tmp_path: Path) -> None:
    _app()
    root = tmp_path / "Portable Workspace"
    created = ProjectWorkspace.create(root, "Portable")
    created.import_source(FIXTURES / "panorama" / "basic_panorama.xml")

    window = MainWindow()
    reopened = window.load_workspace(root)

    assert reopened.manifest.name == "Portable"
    assert window.sources_view.sources_table.rowCount() == 1
    assert window.explorer.tree.topLevelItemCount() == 1
    assert window.import_source_action.isEnabled()
    assert window.export_xml_action.isEnabled()


def test_project_context_menu_separates_project_and_xml_actions(tmp_path: Path) -> None:
    _app()
    workspace = ProjectWorkspace.create(tmp_path / "Context Project", "Context Project")
    window = MainWindow()
    window.load_workspace(workspace)
    project_item = window.explorer.tree.topLevelItem(0)

    empty_project_menu = window.explorer.build_context_menu(project_item)
    empty_actions = {
        action.text(): action for action in empty_project_menu.actions() if not action.isSeparator()
    }

    assert set(empty_actions) == {
        "New Project…",
        "Open Project…",
        "Import XML…",
        "Export XML…",
    }
    assert empty_actions["Import XML…"].isEnabled()
    assert not empty_actions["Export XML…"].isEnabled()

    window.import_source_path(FIXTURES / "panorama" / "basic_panorama.xml")
    project_item = window.explorer.tree.topLevelItem(0)
    populated_menu = window.explorer.build_context_menu(project_item)
    populated_actions = {
        action.text(): action for action in populated_menu.actions() if not action.isSeparator()
    }

    assert populated_actions["Export XML…"].isEnabled()
