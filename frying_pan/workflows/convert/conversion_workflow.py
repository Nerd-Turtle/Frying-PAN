from __future__ import annotations

from frying_pan.workflows.convert.conversion_plan import ConversionDecision, ConversionPlan


class ConversionWorkflow:
    def create_plan(self, source_config_id: str) -> ConversionPlan:
        return ConversionPlan(source_config_id=source_config_id)

    def stage_decision(self, plan: ConversionPlan, decision: ConversionDecision) -> ConversionPlan:
        plan.decisions.append(decision)
        return plan
