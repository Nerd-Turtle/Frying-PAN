from __future__ import annotations

from frying_pan.gui.migrate.drag_drop import create_copy_object_decision
from frying_pan.workflows.migrate.migration_plan import MigrationAction, MigrationPlan


def test_drag_drop_creates_staged_migration_decision() -> None:
    decision = create_copy_object_decision("src/WebServers", "dst/DG-A/AddressGroups")
    plan = MigrationPlan(source_config_ids=["src"], target_config_id="dst", decisions=[decision])

    assert plan.decisions[0].action == MigrationAction.COPY_OBJECT
    assert "not mutated" in plan.decisions[0].warnings[0]
