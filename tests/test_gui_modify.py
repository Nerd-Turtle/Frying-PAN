from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from frying_pan.gui.modify.modify_workspace import ModifyWorkspace
from frying_pan.normalized.rules import RulebaseType
from frying_pan.sources.parsing import parse_source
from frying_pan.workflows.modify.modify_workflow import ModifyWorkflow


def _app() -> QApplication:
    app = QApplication.instance()
    return app if app is not None else QApplication([])


def test_modify_workspace_displays_staged_plan_offscreen() -> None:
    _app()
    config = parse_source(Path("tests/fixtures/firewall/reference_config_items_virtual_router.xml"))
    workflow = ModifyWorkflow()
    plan = workflow.create_plan_from_config(config)
    workflow.stage_rule_reorder(
        config,
        plan,
        scope_path="vsys/vsys1",
        rulebase_type=RulebaseType.SECURITY_LOCAL,
        rule_name="FP-REF-FW-DROP-CLEANUP",
        new_position=1,
    )
    workflow.validate_plan(config, plan)

    workspace = ModifyWorkspace()
    workspace.set_plan(plan)

    assert "Actions: 1" in workspace.summary_label.text()
    assert workspace.plan_view.rowCount() == 1
