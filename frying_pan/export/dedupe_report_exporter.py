from __future__ import annotations

from pathlib import Path

from frying_pan.analysis.dedupe_models import DedupeAnalysisResult


def export_dedupe_analysis_markdown(
    result: DedupeAnalysisResult, output_path: Path
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_dedupe_analysis_markdown(result), encoding="utf-8")
    return output_path


def render_dedupe_analysis_markdown(result: DedupeAnalysisResult) -> str:
    lines = [
        "# Frying-PAN Dedupe And Conflict Analysis",
        "",
        "This report is generated from imported configuration inventory only. "
        "Findings are advisory and do not stage or mutate XML.",
        "",
        "## Source",
        "",
        f"- Source ID: `{result.source_id}`",
        f"- Source type: `{result.source_type or 'unknown'}`",
        f"- Analyzed objects: {result.analyzed_object_count}",
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
            lines.extend(
                [
                    f"### {finding.finding_id or finding.finding_type.value}",
                    "",
                    f"- Type: `{finding.finding_type.value}`",
                    f"- Severity: `{finding.severity.value}`",
                    f"- Object type: `{finding.object_type}`",
                    f"- Objects: {', '.join(finding.object_names) or 'None'}",
                    f"- Scopes: {', '.join(finding.scopes) or 'None'}",
                    f"- Explanation: {finding.explanation}",
                    f"- Recommendation: {finding.recommendation or 'Review manually.'}",
                    "",
                ]
            )
    else:
        lines.append("- No dedupe/conflict findings emitted.")

    lines.extend(["## Warnings And Limitations", ""])
    if result.warnings:
        lines.extend(f"- {warning}" for warning in result.warnings)
    else:
        lines.append("- No dedupe/conflict warnings emitted.")
    lines.extend(
        [
            "- Findings are advisory and must be reviewed before Modify or Migrate staging.",
            "- XML mutation/export remains blocked until serializer tests exist.",
            "",
        ]
    )
    return "\n".join(lines)


def _count_bullets(counts: dict[str, int]) -> list[str]:
    if not counts:
        return ["- None"]
    return [f"- `{name}`: {count}" for name, count in sorted(counts.items())]
