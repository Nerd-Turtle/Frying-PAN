from __future__ import annotations

from pydantic import BaseModel, Field

from frying_pan.normalized.rules import RuleAction, SecurityRule
from frying_pan.policy.match.match_trace import MatchTraceStep


class PolicyMatchResult(BaseModel):
    matched_rule: SecurityRule | None = None
    action: RuleAction = RuleAction.UNKNOWN
    trace: list[MatchTraceStep] = Field(default_factory=list)
    later_matching_rules: list[SecurityRule] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
