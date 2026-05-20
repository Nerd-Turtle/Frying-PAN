from __future__ import annotations

from pydantic import BaseModel, Field


class ConversionWarning(BaseModel):
    code: str
    message: str
    source_location: str | None = None
    confidence: str = "medium"


class UnsupportedFeature(BaseModel):
    feature: str
    source_location: str | None = None
    notes: str | None = None
    warnings: list[str] = Field(default_factory=list)
