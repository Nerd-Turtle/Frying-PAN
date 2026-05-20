from __future__ import annotations

from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class MigrationAction(StrEnum):
    COPY_OBJECT = "copy_object"
    MAP_OBJECT = "map_object"
    MAP_ZONE = "map_zone"
    COPY_RULE = "copy_rule"
    PLACE_RULE = "place_rule"
    INCLUDE_DEPENDENCY = "include_dependency"
    SKIP = "skip"


class PlanDecision(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    action: MigrationAction
    source_ref: str
    target_ref: str | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    approved: bool = False


class MigrationPlan(BaseModel):
    source_config_ids: list[str]
    target_config_id: str
    decisions: list[PlanDecision] = Field(default_factory=list)
    assurance_required: bool = True
