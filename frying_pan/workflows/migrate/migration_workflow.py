from __future__ import annotations

from frying_pan.workflows.migrate.migration_plan import MigrationPlan, PlanDecision


class MigrationWorkflow:
    def create_plan(self, source_config_ids: list[str], target_config_id: str) -> MigrationPlan:
        return MigrationPlan(source_config_ids=source_config_ids, target_config_id=target_config_id)

    def stage_decision(self, plan: MigrationPlan, decision: PlanDecision) -> MigrationPlan:
        plan.decisions.append(decision)
        return plan
