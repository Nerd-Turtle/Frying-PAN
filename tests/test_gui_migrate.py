from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from frying_pan.gui.migrate.migration_workspace import MigrationWorkspace
from frying_pan.sources.parsing import parse_source
from frying_pan.workflows.migrate.migration_workflow import MigrationWorkflow


def _app() -> QApplication:
    app = QApplication.instance()
    return app if app is not None else QApplication([])


def test_migration_workspace_displays_staged_plan_offscreen() -> None:
    _app()
    source = parse_source(
        Path("tests/fixtures/firewall/reference_config_items_virtual_router.xml")
    )
    target = parse_source(
        Path("tests/fixtures/firewall/reference_config_items_virtual_router.xml")
    )
    workflow = MigrationWorkflow()
    plan = workflow.create_plan_from_configs(source, target)
    workflow.stage_scope_mapping(plan, "vsys/vsys1", "vsys/vsys1")
    workflow.validate_plan(source, target, plan)

    workspace = MigrationWorkspace()
    workspace.set_plan(plan)

    assert "Mappings: 1" in workspace.summary_label.text()
    assert workspace.mapping_table.rowCount() == 1
