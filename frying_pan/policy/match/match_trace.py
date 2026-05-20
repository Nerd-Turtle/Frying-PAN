from __future__ import annotations

from pydantic import BaseModel, Field


class MatchTraceStep(BaseModel):
    rule_name: str
    matched: bool
    reason: str
    warnings: list[str] = Field(default_factory=list)
