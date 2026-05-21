from __future__ import annotations

from pathlib import Path

from frying_pan.workflows.convert.conversion_plan import ConversionPlan
from frying_pan.workflows.convert.converted_import import ConvertedImportPackage


def export_conversion_report_markdown(
    package: ConvertedImportPackage,
    plan: ConversionPlan,
    output_path: Path,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        render_conversion_report_markdown(package, plan), encoding="utf-8"
    )
    return output_path


def render_conversion_report_markdown(
    package: ConvertedImportPackage, plan: ConversionPlan
) -> str:
    lines = [
        "# Frying-PAN Conversion Report",
        "",
        "This report describes a local converted import package. It does not mutate "
        "source files or export production Palo Alto XML.",
        "",
        "## Summary",
        "",
        f"- Package ID: `{package.package_id}`",
        f"- Name: `{package.name}`",
        f"- Source format: `{package.source_format}`",
        f"- Source path: `{package.source_path or 'unknown'}`",
        f"- Source config ID: `{package.normalized_config.source_id}`",
        f"- Scopes: {package.scope_count}",
        f"- Entities: {package.entity_count}",
        f"- Security rules: {package.security_rule_count}",
        f"- References: {len(package.normalized_config.references)}",
        f"- Warnings: {package.warning_count}",
        f"- Unsupported features: {package.unsupported_count}",
        f"- Validation errors: {len(package.validation.errors)}",
        f"- Validation warnings: {len(package.validation.warnings)}",
        f"- Plan decisions: {plan.decision_count}",
        "",
        "## Validation",
        "",
    ]
    if package.validation.errors:
        lines.extend(f"- Error: {error}" for error in package.validation.errors)
    if package.validation.warnings:
        lines.extend(f"- Warning: {warning}" for warning in package.validation.warnings)
    if not package.validation.errors and not package.validation.warnings:
        lines.append("- No validation messages.")

    lines.extend(["", "## Conversion Warnings", ""])
    if package.warnings:
        for warning in package.warnings:
            lines.append(
                f"- `{warning.severity.value}` `{warning.code}`: {warning.message}"
            )
    else:
        lines.append("- None")

    lines.extend(["", "## Unsupported Features", ""])
    if package.unsupported_features:
        for feature in package.unsupported_features:
            lines.append(
                f"- `{feature.feature}` at `{feature.source_location or 'unknown'}`: "
                f"{feature.notes or 'Review required.'}"
            )
    else:
        lines.append("- None")

    lines.extend(["", "## Plan Decisions", ""])
    if plan.decisions:
        for decision in plan.decisions:
            lines.append(
                f"- `{decision.action.value}` from `{decision.source_ref}` "
                f"approved=`{decision.approved}`"
            )
    else:
        lines.append("- None")

    lines.extend(["", "## Limitations", ""])
    lines.append(
        "- Generic JSON conversion is a framework validation path, not "
        "vendor-complete migration."
    )
    lines.append("- XML mutation/export remains blocked until serializer tests exist.")
    lines.append("")
    return "\n".join(lines)
