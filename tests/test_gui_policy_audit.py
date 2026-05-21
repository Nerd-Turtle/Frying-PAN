from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from frying_pan.gui.policy_audit.audit_workspace import AuditWorkspace
from frying_pan.normalized.config import NormalizedConfig
from frying_pan.normalized.rules import RuleAction, RulebaseType, SecurityRule
from frying_pan.normalized.scope import ConfigScope, ScopeType
from frying_pan.policy.audit.audit_engine import PolicyAuditEngine
from frying_pan.sources.base import SourceType


def _app() -> QApplication:
    app = QApplication.instance()
    return app if app is not None else QApplication([])


def test_policy_audit_workspace_displays_result_offscreen() -> None:
    _app()
    workspace = AuditWorkspace()
    config = NormalizedConfig(
        source_id="source-1",
        source_type=SourceType.FIREWALL_XML,
        scopes=[ConfigScope(name="vsys1", scope_type=ScopeType.VSYS, path="vsys/vsys1")],
        security_rules=[
            SecurityRule(
                name="allow-any",
                scope_path="vsys/vsys1",
                rulebase_type=RulebaseType.SECURITY_LOCAL,
                position=1,
                action=RuleAction.ALLOW,
            )
        ],
    )
    result = PolicyAuditEngine().audit_config(config, "vsys/vsys1")

    workspace.set_result(result)

    assert "Findings:" in workspace.summary_label.text()
    assert workspace.findings_table.rowCount() == result.finding_count
    assert "BROAD_ALLOW" in workspace.detail_view.body_label.text()
