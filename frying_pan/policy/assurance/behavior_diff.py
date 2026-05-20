from __future__ import annotations

from pydantic import BaseModel, Field

from frying_pan.policy.assurance.behavior_snapshot import BehaviorSnapshot


class BehaviorDiff(BaseModel):
    before: BehaviorSnapshot
    after: BehaviorSnapshot
    behavior_changed: bool
    warnings: list[str] = Field(default_factory=list)
