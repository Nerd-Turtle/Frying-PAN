from __future__ import annotations

from pathlib import Path

from frying_pan.export.policy_audit_exporter import (
    export_policy_audit_markdown,
    render_policy_audit_markdown,
)
from frying_pan.normalized.rules import RuleAction, SecurityRule
from frying_pan.policy.audit.audit_engine import PolicyAuditEngine


def test_policy_audit_markdown_report(tmp_path: Path) -> None:
    result = PolicyAuditEngine().audit_config(
        _single_rule_config(), "vsys/vsys1"
    )

    report_text = render_policy_audit_markdown(result)
    report_path = export_policy_audit_markdown(result, tmp_path / "audit.md")

    assert "# Frying-PAN Policy Audit Report" in report_text
    assert "Findings are review signals" in report_text
    assert "BROAD_ALLOW" in report_path.read_text(encoding="utf-8")


def _single_rule_config():
    from frying_pan.normalized.config import NormalizedConfig
    from frying_pan.normalized.rules import RulebaseType
    from frying_pan.normalized.scope import ConfigScope, ScopeType
    from frying_pan.sources.base import SourceType

    return NormalizedConfig(
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
