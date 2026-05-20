from __future__ import annotations

from frying_pan.workflows.convert.conversion_plan import (
    ConversionAction,
    ConversionDecision,
    ConversionPlan,
)


def test_conversion_plan_records_warning_decisions() -> None:
    decision = ConversionDecision(
        action=ConversionAction.ACCEPT_WARNING,
        source_ref="fortigate/policy/1",
        warnings=["Lossy conversion requires operator review."],
    )
    plan = ConversionPlan(source_config_id="vendor", decisions=[decision])

    assert plan.decisions[0].warnings
