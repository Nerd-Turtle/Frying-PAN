from __future__ import annotations

from pydantic import BaseModel


class RuleMapping(BaseModel):
    source_rule_ref: str
    target_rulebase_ref: str
    insert_after_rule_ref: str | None = None
    insert_before_rule_ref: str | None = None
