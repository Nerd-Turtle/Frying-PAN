from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class ConversionWarningSeverity(StrEnum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ConversionWarning(BaseModel):
    code: str
    message: str
    source_location: str | None = None
    source_field: str | None = None
    normalized_target: str | None = None
    severity: ConversionWarningSeverity = ConversionWarningSeverity.MEDIUM
    confidence: str = "medium"
    suggested_review: str | None = None


class UnsupportedFeature(BaseModel):
    feature: str
    source_location: str | None = None
    notes: str | None = None
    warnings: list[str] = Field(default_factory=list)
