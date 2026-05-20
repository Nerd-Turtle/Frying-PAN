from __future__ import annotations

from frying_pan.normalized.rules import RuleAction
from frying_pan.panos.normalizers.security_rule import normalize_security_rule


def test_security_rule_normalizer_is_conservative() -> None:
    rule = normalize_security_rule("Allow-App", "shared", 10)

    assert rule.action == RuleAction.UNKNOWN
    assert rule.position == 10
