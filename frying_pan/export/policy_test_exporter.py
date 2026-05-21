from __future__ import annotations

from pathlib import Path

from frying_pan.policy.match.result import PolicyMatchResult
from frying_pan.policy.match.test_case import PolicyTestCase


def export_policy_test_markdown(
    test_case: PolicyTestCase, result: PolicyMatchResult, output_path: Path
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_policy_test_markdown(test_case, result), encoding="utf-8")
    return output_path


def render_policy_test_markdown(test_case: PolicyTestCase, result: PolicyMatchResult) -> str:
    matched_rule = result.matched_rule.name if result.matched_rule else "None"
    lines = [
        "# Frying-PAN Policy Test Result",
        "",
        "This report is generated from imported configuration data only. "
        "It does not simulate all PAN-OS runtime state.",
        "",
        "## Test Flow",
        "",
        f"- Source zone: `{test_case.source_zone}`",
        f"- Destination zone: `{test_case.destination_zone}`",
        f"- Source IP: `{test_case.source_ip}`",
        f"- Destination IP: `{test_case.destination_ip}`",
        f"- Protocol: `{test_case.protocol}`",
        f"- Destination port: `{test_case.destination_port}`",
        f"- Source port: `{test_case.source_port}`",
        f"- Application: `{test_case.application}`",
        f"- User: `{test_case.user}`",
        f"- URL category: `{test_case.url_category or 'any'}`",
        "",
        "## Result",
        "",
        f"- Scope: `{result.scope_path or 'direct rule list'}`",
        f"- Matched rule: `{matched_rule}`",
        f"- Action: `{result.action}`",
        f"- Evaluated rules: {result.evaluated_rule_count}",
        f"- Later matching rules: {len(result.later_matching_rules)}",
        "",
        "## Trace",
        "",
    ]
    if result.trace:
        for step in result.trace:
            marker = "matched" if step.matched else "skipped"
            lines.append(f"- `{step.rule_name}`: {marker}; {step.reason}")
    else:
        lines.append("- No rules were evaluated.")

    lines.extend(["", "## Warnings And Limitations", ""])
    if result.warnings:
        lines.extend(f"- {warning}" for warning in result.warnings)
    else:
        lines.append("- No policy tester warnings emitted.")
    lines.append("")
    return "\n".join(lines)
