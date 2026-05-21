from __future__ import annotations

from pathlib import Path

from frying_pan.workflows.modify.actions import ModifyPlanPreview
from frying_pan.workflows.modify.modify_plan import ModificationPlan


def export_modify_plan_markdown(
    plan: ModificationPlan, preview: ModifyPlanPreview, output_path: Path
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_modify_plan_markdown(plan, preview), encoding="utf-8")
    return output_path


def render_modify_plan_markdown(plan: ModificationPlan, preview: ModifyPlanPreview) -> str:
    lines = [
        "# Frying-PAN Modify Plan",
        "",
        "This report describes staged modification decisions only. It does not mutate "
        "source XML and is not production XML export.",
        "",
        "## Summary",
        "",
        f"- Source config ID: `{plan.source_config_id}`",
        f"- Source type: `{plan.source_type or 'unknown'}`",
        f"- Status: `{plan.status.value}`",
        f"- Actions: {plan.action_count}",
        f"- Approved actions: {plan.approved_action_count}",
        f"- Validation messages: {len(plan.validation.messages)}",
        "",
        "## Actions",
        "",
    ]
    if plan.decisions:
        for decision, summary in zip(plan.decisions, preview.action_summaries, strict=False):
            lines.extend(
                [
                    f"### {decision.id}",
                    "",
                    f"- Summary: {summary}",
                    f"- Status: `{decision.status.value}`",
                    f"- Approved: `{decision.approved}`",
                    f"- Impacted references: {len(decision.impacted_references)}",
                    "",
                ]
            )
    else:
        lines.append("- No staged actions.")

    lines.extend(["## Validation", ""])
    if plan.validation.messages:
        for message in plan.validation.messages:
            lines.append(f"- `{message.level.value}`: {message.message}")
    else:
        lines.append("- No validation messages.")

    lines.extend(["", "## Warnings And Limitations", ""])
    for warning in preview.warnings:
        lines.append(f"- {warning}")
    lines.append("- XML mutation/export remains blocked until serializer tests exist.")
    lines.append("")
    return "\n".join(lines)
