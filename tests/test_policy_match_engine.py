from __future__ import annotations

from frying_pan.normalized.rules import RuleAction, SecurityRule
from frying_pan.policy.match.match_engine import PolicyMatchEngine
from frying_pan.policy.match.test_case import PolicyTestCase


def test_policy_match_engine_uses_first_match() -> None:
    rules = [
        SecurityRule(name="allow-first", scope_path="shared", position=1, action=RuleAction.ALLOW),
        SecurityRule(name="deny-later", scope_path="shared", position=2, action=RuleAction.DENY),
    ]
    test_case = PolicyTestCase(
        source_zone="trust",
        destination_zone="untrust",
        source_ip="192.0.2.10",
        destination_ip="198.51.100.20",
        protocol="tcp",
        destination_port=443,
    )

    result = PolicyMatchEngine().evaluate(rules, test_case)

    assert result.matched_rule is not None
    assert result.matched_rule.name == "allow-first"
    assert result.action == RuleAction.ALLOW
    assert [rule.name for rule in result.later_matching_rules] == ["deny-later"]
