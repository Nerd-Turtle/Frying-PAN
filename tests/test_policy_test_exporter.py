from __future__ import annotations

from pathlib import Path

from frying_pan.export.policy_test_exporter import (
    export_policy_test_markdown,
    render_policy_test_markdown,
)
from frying_pan.normalized.rules import RuleAction, SecurityRule
from frying_pan.policy.match.match_engine import PolicyMatchEngine
from frying_pan.policy.match.test_case import PolicyTestCase


def test_policy_test_markdown_report(tmp_path: Path) -> None:
    test_case = PolicyTestCase(
        source_zone="trust",
        destination_zone="untrust",
        source_ip="192.0.2.1",
        destination_ip="198.51.100.10",
        protocol="tcp",
        destination_port=443,
    )
    result = PolicyMatchEngine().evaluate(
        [
            SecurityRule(
                name="allow-web",
                scope_path="shared",
                position=1,
                action=RuleAction.ALLOW,
            )
        ],
        test_case,
    )

    report_text = render_policy_test_markdown(test_case, result)
    report_path = export_policy_test_markdown(test_case, result, tmp_path / "policy-test.md")

    assert "# Frying-PAN Policy Test Result" in report_text
    assert "Matched rule: `allow-web`" in report_path.read_text(encoding="utf-8")
    assert "does not simulate all PAN-OS runtime state" in report_text
