from __future__ import annotations

from pathlib import Path

from frying_pan.analysis.inventory import InventorySummary, summarize_inventory
from frying_pan.normalized.config import NormalizedConfig


def export_inventory_markdown(
    summary_or_config: InventorySummary | NormalizedConfig, output_path: Path
) -> Path:
    summary = (
        summarize_inventory(summary_or_config)
        if isinstance(summary_or_config, NormalizedConfig)
        else summary_or_config
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_inventory_markdown(summary), encoding="utf-8")
    return output_path


def render_inventory_markdown(summary: InventorySummary) -> str:
    lines = [
        "# Frying-PAN Inventory Report",
        "",
        "This report is generated from imported configuration inventory only. "
        "It does not imply XML mutation, migration, or production-safe export support.",
        "",
        "## Source",
        "",
        f"- Source ID: `{summary.source_id}`",
        f"- Source type: `{summary.source_type}`",
        "",
        "## Summary",
        "",
        f"- Scopes: {summary.scope_count}",
        f"- Entities: {summary.entity_count}",
        f"- Security rules: {summary.security_rule_count}",
        f"- References: {summary.reference_count}",
        f"- Dependencies: {summary.dependency_count}",
        f"- Unresolved references: {summary.unresolved_reference_count}",
        f"- Parser warnings: {summary.warning_count}",
        "",
        "## Scopes",
        "",
    ]
    lines.extend(_bullets(summary.scopes))
    lines.extend(["", "## Entity Counts", ""])
    lines.extend(_count_bullets(summary.entity_counts_by_type))
    lines.extend(["", "## Security Rule Counts", ""])
    lines.extend(_count_bullets(summary.security_rule_counts_by_rulebase))
    lines.extend(["", "## Warnings And Limitations", ""])
    if summary.warnings:
        lines.extend(_bullets(summary.warnings))
    else:
        lines.append("- No parser warnings emitted.")
    lines.extend(
        [
            "- XML mutation/export remains blocked until serializer tests exist.",
            "- Offline policy behavior remains conservative where runtime context is unavailable.",
            "",
        ]
    )
    return "\n".join(lines)


def _bullets(values: list[str]) -> list[str]:
    if not values:
        return ["- None"]
    return [f"- {value}" for value in values]


def _count_bullets(counts: dict[str, int]) -> list[str]:
    if not counts:
        return ["- None"]
    return [f"- `{name}`: {count}" for name, count in sorted(counts.items())]
