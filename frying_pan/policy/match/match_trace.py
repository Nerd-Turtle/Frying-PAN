from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from frying_pan.normalized.rules import RuleAction


class MatchTraceStep(BaseModel):
    rule_name: str
    matched: bool
    reason: str
    warnings: list[str] = Field(default_factory=list)
    criteria: dict[str, bool] = Field(default_factory=dict)
    details: list[str] = Field(default_factory=list)
    position: int | None = None
    rulebase_type: str | None = None
    action: RuleAction | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
