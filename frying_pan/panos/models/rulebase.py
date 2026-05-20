from __future__ import annotations

from pydantic import BaseModel, Field

from frying_pan.normalized.rules import RulebaseType, SecurityRule


class Rulebase(BaseModel):
    scope_path: str
    rulebase_type: RulebaseType
    security_rules: list[SecurityRule] = Field(default_factory=list)
