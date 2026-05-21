from __future__ import annotations

from pathlib import Path

import pytest

from frying_pan.export.migration_plan_exporter import (
    export_migration_plan_markdown,
    render_migration_plan_markdown,
)
from frying_pan.gui.migrate.drag_drop import create_copy_object_decision
from frying_pan.policy.match.test_case import PolicyTestCase
from frying_pan.sources.parsing import parse_source
from frying_pan.workflows.migrate.migration_plan import (
    MigrationAction,
    MigrationPlan,
    MigrationPlanStatus,
    MigrationValidationLevel,
)
from frying_pan.workflows.migrate.migration_workflow import MigrationWorkflow
from frying_pan.workflows.migrate.object_mapping import ObjectMapping, ObjectMappingMode
from frying_pan.workflows.migrate.rule_mapping import RuleMapping, RulePlacementMode

FIXTURES = Path(__file__).parent / "fixtures"
FIREWALL_FIXTURE = FIXTURES / "firewall" / "reference_config_items_virtual_router.xml"


def test_drag_drop_creates_staged_migration_decision() -> None:
    decision = create_copy_object_decision("src/WebServers", "dst/DG-A/AddressGroups")
    plan = MigrationPlan(source_config_ids=["src"], target_config_id="dst", decisions=[decision])

    assert plan.decisions[0].action == MigrationAction.COPY_OBJECT
    assert "not mutated" in plan.decisions[0].warnings[0]


def test_migration_mapping_models_validate_required_targets_and_anchors() -> None:
    with pytest.raises(ValueError):
        ObjectMapping(source_object_ref="src", mode=ObjectMappingMode.REUSE_TARGET)

    with pytest.raises(ValueError):
        RuleMapping(
            source_rule_ref="source-rule",
            target_rulebase_ref="target-rulebase",
            placement_mode=RulePlacementMode.INSERT_AFTER,
        )


def test_migration_workflow_stages_mappings_dependencies_and_validation() -> None:
    source = parse_source(FIREWALL_FIXTURE)
    target = parse_source(FIREWALL_FIXTURE)
    workflow = MigrationWorkflow()
    plan = workflow.create_plan_from_configs(source, target)

    workflow.stage_scope_mapping(plan, "vsys/vsys1", "vsys/vsys1")
    workflow.stage_zone_mapping(plan, "FP-REF-FW-ZONE-TRUST", "FP-REF-FW-ZONE-TRUST")
    workflow.stage_object_mapping(
        plan,
        "vsys/vsys1::address_object::FP-REF-FW-ADDR-USERS-10.60.10.0_24",
        target_object_ref="vsys/vsys1::address_object::FP-REF-FW-ADDR-USERS-10.60.10.0_24",
        mode=ObjectMappingMode.REUSE_TARGET,
    )
    workflow.stage_rule_placement(
        plan,
        "vsys/vsys1::security_local::FP-REF-FW-ALLOW-USERS-TO-DMZ-WEB",
        "vsys/vsys1::security_local",
    )
    workflow.include_dependencies(source, plan, "FP-REF-FW-ALLOW-USERS-TO-DMZ-WEB")
    validation = workflow.validate_plan(source, target, plan)

    assert plan.mapping_count == 4
    assert plan.dependency_refs
    assert plan.status == MigrationPlanStatus.READY_FOR_REVIEW
    assert validation.has_warnings


def test_migration_workflow_blocks_missing_scope_and_object() -> None:
    source = parse_source(FIREWALL_FIXTURE)
    target = parse_source(FIREWALL_FIXTURE)
    workflow = MigrationWorkflow()
    plan = workflow.create_plan_from_configs(source, target)

    workflow.stage_scope_mapping(plan, "missing-source", "missing-target")
    workflow.stage_object_mapping(
        plan,
        "vsys/vsys1::address_object::MISSING",
        target_object_ref="vsys/vsys1::address_object::MISSING",
        mode=ObjectMappingMode.REUSE_TARGET,
    )
    validation = workflow.validate_plan(source, target, plan)

    assert validation.has_errors
    assert plan.status == MigrationPlanStatus.BLOCKED
    assert any(
        message.level == MigrationValidationLevel.ERROR for message in validation.messages
    )


def test_migration_policy_assurance_compare_and_preview() -> None:
    source = parse_source(FIREWALL_FIXTURE)
    target = parse_source(FIREWALL_FIXTURE)
    workflow = MigrationWorkflow()
    plan = workflow.create_plan_from_configs(source, target)
    test_case = PolicyTestCase(
        source_zone="FP-REF-FW-ZONE-TRUST",
        destination_zone="FP-REF-FW-ZONE-DMZ",
        source_ip="10.60.10.10",
        destination_ip="10.70.10.10",
        protocol="tcp",
        destination_port=443,
        application="web-browsing",
        url_category="FP-REF-FW-URLCAT-EXAMPLE",
    )

    diff = workflow.compare_test_flow(
        source,
        target,
        plan,
        test_case,
        source_scope_path="vsys/vsys1",
        target_scope_path="vsys/vsys1",
    )
    preview = workflow.preview_plan(plan)

    assert diff.behavior_changed is False
    assert plan.assurance_results
    assert preview.export_blocked is True
    assert preview.assurance_summaries == ["unchanged"]


def test_migration_plan_markdown_report(tmp_path: Path) -> None:
    source = parse_source(FIREWALL_FIXTURE)
    target = parse_source(FIREWALL_FIXTURE)
    workflow = MigrationWorkflow()
    plan = workflow.create_plan_from_configs(source, target)
    workflow.stage_scope_mapping(plan, "vsys/vsys1", "vsys/vsys1")
    workflow.validate_plan(source, target, plan)
    preview = workflow.preview_plan(plan)

    report_text = render_migration_plan_markdown(plan, preview)
    report_path = export_migration_plan_markdown(plan, preview, tmp_path / "migration.md")

    assert "# Frying-PAN Migration Plan" in report_text
    assert "does not mutate source or target XML" in report_path.read_text(encoding="utf-8")
