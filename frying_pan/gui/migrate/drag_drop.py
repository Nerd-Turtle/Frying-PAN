from __future__ import annotations

from frying_pan.workflows.migrate.migration_plan import MigrationAction, PlanDecision


def create_copy_object_decision(source_ref: str, target_ref: str) -> PlanDecision:
    return PlanDecision(
        action=MigrationAction.COPY_OBJECT,
        source_ref=source_ref,
        target_ref=target_ref,
        warnings=["Decision is staged only; source XML is not mutated by drag/drop."],
    )
