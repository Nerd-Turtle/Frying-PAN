from __future__ import annotations

from pydantic import BaseModel

from frying_pan.normalized.rules import RuleAction
from frying_pan.policy.match.test_case import PolicyTestCase


class BehaviorSnapshot(BaseModel):
    test_case: PolicyTestCase
    matched_rule_name: str | None
    action: RuleAction
