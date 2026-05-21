from __future__ import annotations

from pydantic import BaseModel, Field

from frying_pan.workflows.modify.modify_plan import ModifyPlanDecision


class PlannedActionResult(BaseModel):
    action_id: str
    safe_to_apply: bool = False
    warnings: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class ModifyPlanPreview(BaseModel):
    source_config_id: str
    action_summaries: list[str] = Field(default_factory=list)
    impacted_reference_summaries: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    export_blocked: bool = True


def summarize_decision(decision: ModifyPlanDecision) -> str:
    target = f" -> {decision.target_ref}" if decision.target_ref else ""
    return f"{decision.action.value}: {decision.source_ref}{target}"
