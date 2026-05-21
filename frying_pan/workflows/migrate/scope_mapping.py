from __future__ import annotations

from pydantic import BaseModel, Field


class ScopeMapping(BaseModel):
    source_scope_path: str
    target_scope_path: str
    notes: str | None = None
    warnings: list[str] = Field(default_factory=list)


class ZoneMapping(BaseModel):
    source_zone: str
    target_zone: str
    source_scope_path: str | None = None
    target_scope_path: str | None = None
    warnings: list[str] = Field(default_factory=list)
