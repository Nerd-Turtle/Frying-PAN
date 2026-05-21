from __future__ import annotations

from pathlib import Path

import pytest

from frying_pan.export.modify_plan_exporter import (
    export_modify_plan_markdown,
    render_modify_plan_markdown,
)
from frying_pan.normalized.rules import RulebaseType
from frying_pan.sources.parsing import parse_source
from frying_pan.workflows.modify.modify_plan import (
    ModificationPlan,
    ModifyAction,
    ModifyPlanDecision,
    ModifyPlanStatus,
    ValidationLevel,
)
from frying_pan.workflows.modify.modify_workflow import ModifyWorkflow

FIXTURES = Path(__file__).parent / "fixtures"


def test_modify_plan_stages_decision_without_approval() -> None:
    decision = ModifyPlanDecision(
        action=ModifyAction.RENAME_OBJECT,
        source_ref="shared::address_object::old",
        target_ref="shared::address_object::new",
    )
    plan = ModificationPlan(source_config_id="src", decisions=[decision])

    assert plan.decisions[0].approved is False
    assert plan.action_count == 1


def test_modify_action_requires_target_for_object_changes() -> None:
    with pytest.raises(ValueError):
        ModifyPlanDecision(
            action=ModifyAction.RENAME_OBJECT,
            source_ref="shared::address_object::old",
        )


def test_modify_workflow_stages_rename_with_impacted_references() -> None:
    config = parse_source(FIXTURES / "firewall" / "reference_config_items_virtual_router.xml")
    workflow = ModifyWorkflow()
    plan = workflow.create_plan_from_config(config)

    workflow.stage_object_rename(
        config,
        plan,
        scope_path="vsys/vsys1",
        entity_type="address_object",
        object_name="FP-REF-FW-ADDR-USERS-10.60.10.0_24",
        new_name="FP-REF-FW-ADDR-USERS-RENAMED",
    )
    validation = workflow.validate_plan(config, plan)

    assert plan.status == ModifyPlanStatus.READY_FOR_REVIEW
    assert plan.decisions[0].impacted_references
    assert any(message.level == ValidationLevel.WARNING for message in validation.messages)


def test_modify_workflow_blocks_missing_source_and_duplicate_actions() -> None:
    config = parse_source(FIXTURES / "firewall" / "reference_config_items_virtual_router.xml")
    workflow = ModifyWorkflow()
    plan = workflow.create_plan_from_config(config)

    for _ in range(2):
        workflow.stage_object_rename(
            config,
            plan,
            scope_path="vsys/vsys1",
            entity_type="address_object",
            object_name="MISSING",
            new_name="NEW",
        )
    validation = workflow.validate_plan(config, plan)

    assert validation.has_errors
    assert plan.status == ModifyPlanStatus.BLOCKED


def test_modify_workflow_stages_move_dedupe_reorder_and_metadata() -> None:
    config = parse_source(FIXTURES / "firewall" / "reference_config_items_virtual_router.xml")
    workflow = ModifyWorkflow()
    plan = workflow.create_plan_from_config(config)

    workflow.stage_object_move(
        config,
        plan,
        source_scope_path="vsys/vsys1",
        target_scope_path="shared",
        entity_type="address_object",
        object_name="FP-REF-FW-ADDR-DMZ-WEB-10.70.10.10",
    )
    workflow.stage_object_dedupe(
        config,
        plan,
        duplicate_scope_path="vsys/vsys1",
        entity_type="address_object",
        duplicate_name="FP-REF-FW-ADDR-DMZ-API-10.70.10.20",
        canonical_scope_path="vsys/vsys1",
        canonical_name="FP-REF-FW-ADDR-DMZ-WEB-10.70.10.10",
    )
    workflow.stage_rule_reorder(
        config,
        plan,
        scope_path="vsys/vsys1",
        rulebase_type=RulebaseType.SECURITY_LOCAL,
        rule_name="FP-REF-FW-DROP-CLEANUP",
        new_position=1,
    )
    workflow.stage_rule_metadata(
        config,
        plan,
        scope_path="vsys/vsys1",
        rulebase_type=RulebaseType.SECURITY_LOCAL,
        rule_name="FP-REF-FW-DISABLED-ALLOW-EXAMPLE",
        field="enabled",
        value=True,
    )
    workflow.validate_plan(config, plan)
    preview = workflow.preview_plan(plan)

    assert plan.action_count == 4
    assert preview.export_blocked is True
    assert any("reorder_rule" in summary for summary in preview.action_summaries)


def test_modify_plan_markdown_report(tmp_path: Path) -> None:
    config = parse_source(FIXTURES / "firewall" / "reference_config_items_virtual_router.xml")
    workflow = ModifyWorkflow()
    plan = workflow.create_plan_from_config(config)
    workflow.stage_rule_reorder(
        config,
        plan,
        scope_path="vsys/vsys1",
        rulebase_type=RulebaseType.SECURITY_LOCAL,
        rule_name="FP-REF-FW-DROP-CLEANUP",
        new_position=1,
    )
    workflow.validate_plan(config, plan)
    preview = workflow.preview_plan(plan)

    report_text = render_modify_plan_markdown(plan, preview)
    report_path = export_modify_plan_markdown(plan, preview, tmp_path / "modify.md")

    assert "# Frying-PAN Modify Plan" in report_text
    assert "does not mutate source XML" in report_path.read_text(encoding="utf-8")
