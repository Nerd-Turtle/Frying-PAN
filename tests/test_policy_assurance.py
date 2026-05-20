from __future__ import annotations

from frying_pan.normalized.rules import RuleAction
from frying_pan.policy.assurance.assurance_engine import PolicyAssuranceEngine
from frying_pan.policy.assurance.behavior_snapshot import BehaviorSnapshot
from frying_pan.policy.match.test_case import PolicyTestCase


def _case() -> PolicyTestCase:
    return PolicyTestCase(
        source_zone="trust",
        destination_zone="untrust",
        source_ip="192.0.2.10",
        destination_ip="198.51.100.20",
        protocol="tcp",
        destination_port=443,
    )


def test_policy_assurance_detects_action_change() -> None:
    before = BehaviorSnapshot(test_case=_case(), matched_rule_name="old", action=RuleAction.ALLOW)
    after = BehaviorSnapshot(test_case=_case(), matched_rule_name="new", action=RuleAction.DENY)

    diff = PolicyAssuranceEngine().compare(before, after)

    assert diff.behavior_changed is True
    assert diff.warnings
