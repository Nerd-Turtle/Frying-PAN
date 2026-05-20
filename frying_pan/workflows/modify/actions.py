from __future__ import annotations

from pydantic import BaseModel, Field


class PlannedActionResult(BaseModel):
    action_id: str
    safe_to_apply: bool = False
    warnings: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
