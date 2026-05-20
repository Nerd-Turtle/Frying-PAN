from __future__ import annotations

from pydantic import Field

from frying_pan.normalized.entity import EntityType, NormalizedEntity


class Tag(NormalizedEntity):
    entity_type: EntityType = EntityType.TAG
    color: str | None = None


class Zone(NormalizedEntity):
    entity_type: EntityType = EntityType.ZONE
    interfaces: list[str] = Field(default_factory=list)
