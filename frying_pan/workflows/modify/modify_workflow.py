from __future__ import annotations

from frying_pan.workflows.modify.modify_plan import ModificationPlan, ModifyPlanDecision


class ModifyWorkflow:
    def create_plan(self, source_config_id: str) -> ModificationPlan:
        return ModificationPlan(source_config_id=source_config_id)

    def stage_decision(
        self, plan: ModificationPlan, decision: ModifyPlanDecision
    ) -> ModificationPlan:
        plan.decisions.append(decision)
        return plan
