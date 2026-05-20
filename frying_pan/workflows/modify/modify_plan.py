from __future__ import annotations

from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class ModifyAction(StrEnum):
    RENAME_OBJECT = "rename_object"
    MOVE_OBJECT = "move_object"
    DEDUPE_OBJECT = "dedupe_object"
    CLEAN_UNUSED_OBJECT = "clean_unused_object"
    REORDER_RULE = "reorder_rule"


class ModifyPlanDecision(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    action: ModifyAction
    source_ref: str
    target_ref: str | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    approved: bool = False


class ModificationPlan(BaseModel):
    source_config_id: str
    decisions: list[ModifyPlanDecision] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
