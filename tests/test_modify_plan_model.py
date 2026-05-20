from __future__ import annotations

from frying_pan.workflows.modify.modify_plan import (
    ModificationPlan,
    ModifyAction,
    ModifyPlanDecision,
)


def test_modify_plan_stages_decision_without_approval() -> None:
    decision = ModifyPlanDecision(action=ModifyAction.RENAME_OBJECT, source_ref="shared/old")
    plan = ModificationPlan(source_config_id="src", decisions=[decision])

    assert plan.decisions[0].approved is False
