from __future__ import annotations

from pathlib import Path

from frying_pan.policy.audit.findings import PolicyAuditResult


def export_policy_audit_markdown(result: PolicyAuditResult, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_policy_audit_markdown(result), encoding="utf-8")
    return output_path


def render_policy_audit_markdown(result: PolicyAuditResult) -> str:
    lines = [
        "# Frying-PAN Policy Audit Report",
        "",
        "This report is generated from imported configuration data only. "
        "Findings are review signals and do not mutate XML.",
        "",
        "## Source",
        "",
        f"- Source ID: `{result.source_id}`",
        f"- Source type: `{result.source_type or 'unknown'}`",
        f"- Scope: `{result.scope_path or 'all audited scopes'}`",
        f"- Audited rules: {result.audited_rule_count}",
        f"- Findings: {result.finding_count}",
        "",
        "## Finding Counts By Severity",
        "",
    ]
    lines.extend(_count_bullets(result.finding_counts_by_severity))
    lines.extend(["", "## Finding Counts By Type", ""])
    lines.extend(_count_bullets(result.finding_counts_by_type))
    lines.extend(["", "## Findings", ""])
    if result.findings:
        for finding in result.findings:
            rules = ", ".join(finding.affected_rules) or "None"
            lines.extend(
                [
                    f"### {finding.finding_id or finding.finding_type.value}",
                    "",
                    f"- Type: `{finding.finding_type.value}`",
                    f"- Severity: `{finding.severity.value}`",
                    f"- Rules: {rules}",
                    f"- Explanation: {finding.explanation}",
                    f"- Recommendation: {finding.recommendation or 'Review manually.'}",
                    f"- Confidence: `{finding.confidence}`",
                    "",
                ]
            )
    else:
        lines.append("- No policy audit findings emitted.")

    lines.extend(["## Warnings And Limitations", ""])
    if result.warnings:
        lines.extend(f"- {warning}" for warning in result.warnings)
    else:
        lines.append("- No policy audit warnings emitted.")
    lines.extend(
        [
            "- Audit findings are conservative review signals, not automated remediation.",
            "- XML mutation/export remains blocked until serializer tests exist.",
            "",
        ]
    )
    return "\n".join(lines)


def _count_bullets(counts: dict[str, int]) -> list[str]:
    if not counts:
        return ["- None"]
    return [f"- `{name}`: {count}" for name, count in sorted(counts.items())]
