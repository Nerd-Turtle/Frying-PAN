from __future__ import annotations

from pydantic import BaseModel, Field


class Dependency(BaseModel):
    owner_scope_path: str
    owner_name: str
    owner_type: str
    target_name: str
    target_type_hints: list[str] = Field(default_factory=list)
    resolved: bool = False
    warnings: list[str] = Field(default_factory=list)


class Conflict(BaseModel):
    conflict_type: str
    source_paths: list[str]
    explanation: str
    recommendation: str | None = None
