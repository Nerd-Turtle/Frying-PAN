from __future__ import annotations

from pathlib import Path

from frying_pan.analysis.inventory import InventorySummary


def export_inventory_markdown(summary: InventorySummary, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        "\n".join(
            [
                "# Frying-PAN Inventory Report",
                "",
                f"- Scopes: {summary.scope_count}",
                f"- Entities: {summary.entity_count}",
                f"- Security rules: {summary.security_rule_count}",
                f"- Warnings: {summary.warning_count}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return output_path
