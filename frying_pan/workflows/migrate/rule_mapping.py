from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, model_validator


class RulePlacementMode(StrEnum):
    APPEND = "append"
    INSERT_AFTER = "insert_after"
    INSERT_BEFORE = "insert_before"


class RuleMapping(BaseModel):
    source_rule_ref: str
    target_rulebase_ref: str
    placement_mode: RulePlacementMode = RulePlacementMode.APPEND
    insert_after_rule_ref: str | None = None
    insert_before_rule_ref: str | None = None

    @model_validator(mode="after")
    def _validate_anchors(self) -> RuleMapping:
        if self.placement_mode == RulePlacementMode.INSERT_AFTER and not self.insert_after_rule_ref:
            raise ValueError("insert_after placement requires insert_after_rule_ref.")
        if (
            self.placement_mode == RulePlacementMode.INSERT_BEFORE
            and not self.insert_before_rule_ref
        ):
            raise ValueError("insert_before placement requires insert_before_rule_ref.")
        return self
