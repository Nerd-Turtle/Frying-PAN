from __future__ import annotations

from pathlib import Path

from frying_pan.workflows.migrate.migration_plan import MigrationPlan, MigrationPlanPreview


def export_migration_plan_markdown(
    plan: MigrationPlan, preview: MigrationPlanPreview, output_path: Path
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_migration_plan_markdown(plan, preview), encoding="utf-8")
    return output_path


def render_migration_plan_markdown(
    plan: MigrationPlan, preview: MigrationPlanPreview
) -> str:
    lines = [
        "# Frying-PAN Migration Plan",
        "",
        "This report describes staged migration decisions only. It does not mutate "
        "source or target XML and is not production XML export.",
        "",
        "## Summary",
        "",
        f"- Source config IDs: `{', '.join(plan.source_config_ids)}`",
        f"- Target config ID: `{plan.target_config_id}`",
        f"- Source type: `{plan.source_type or 'unknown'}`",
        f"- Target type: `{plan.target_type or 'unknown'}`",
        f"- Status: `{plan.status.value}`",
        f"- Mappings: {plan.mapping_count}",
        f"- Decisions: {plan.decision_count}",
        f"- Dependencies: {len(plan.dependency_refs)}",
        f"- Assurance comparisons: {len(plan.assurance_results)}",
        f"- Validation messages: {len(plan.validation.messages)}",
        "",
        "## Decisions",
        "",
    ]
    lines.extend(_bullets(preview.decision_summaries))
    lines.extend(["", "## Dependencies", ""])
    lines.extend(_bullets(preview.dependency_summaries))
    lines.extend(["", "## Assurance", ""])
    lines.extend(_bullets(preview.assurance_summaries))
    lines.extend(["", "## Validation", ""])
    if plan.validation.messages:
        lines.extend(
            f"- `{message.level.value}`: {message.message}"
            for message in plan.validation.messages
        )
    else:
        lines.append("- No validation messages.")
    lines.extend(["", "## Warnings And Limitations", ""])
    lines.extend(_bullets(preview.warnings))
    lines.append("- XML mutation/export remains blocked until serializer tests exist.")
    lines.append("")
    return "\n".join(lines)


def _bullets(values: list[str]) -> list[str]:
    if not values:
        return ["- None"]
    return [f"- {value}" for value in values]
