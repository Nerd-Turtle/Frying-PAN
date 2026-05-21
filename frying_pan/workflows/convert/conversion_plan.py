from __future__ import annotations

from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, computed_field


class ConversionAction(StrEnum):
    MAP_ZONE = "map_zone"
    MAP_SERVICE = "map_service"
    MAP_APPLICATION = "map_application"
    ACCEPT_WARNING = "accept_warning"
    SKIP_UNSUPPORTED = "skip_unsupported"
    REVIEW_PACKAGE = "review_package"


class ConversionDecision(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    action: ConversionAction
    source_ref: str
    target_ref: str | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    approved: bool = False


class ConversionPlan(BaseModel):
    source_config_id: str
    package_id: str | None = None
    decisions: list[ConversionDecision] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    @computed_field
    @property
    def decision_count(self) -> int:
        return len(self.decisions)
