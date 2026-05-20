from __future__ import annotations

from pydantic import BaseModel, Field

from frying_pan.normalized.entity import NormalizedEntity
from frying_pan.normalized.references import Conflict, Dependency
from frying_pan.normalized.rules import SecurityRule
from frying_pan.normalized.scope import ConfigScope
from frying_pan.sources.base import SourceType


class NormalizedConfig(BaseModel):
    source_id: str
    source_type: SourceType
    scopes: list[ConfigScope] = Field(default_factory=list)
    entities: list[NormalizedEntity] = Field(default_factory=list)
    security_rules: list[SecurityRule] = Field(default_factory=list)
    dependencies: list[Dependency] = Field(default_factory=list)
    conflicts: list[Conflict] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
