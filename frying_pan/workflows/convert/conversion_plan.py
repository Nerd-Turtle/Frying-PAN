from __future__ import annotations

from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class ConversionAction(StrEnum):
    MAP_ZONE = "map_zone"
    MAP_SERVICE = "map_service"
    MAP_APPLICATION = "map_application"
    ACCEPT_WARNING = "accept_warning"
    SKIP_UNSUPPORTED = "skip_unsupported"


class ConversionDecision(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    action: ConversionAction
    source_ref: str
    target_ref: str | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)


class ConversionPlan(BaseModel):
    source_config_id: str
    decisions: list[ConversionDecision] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
