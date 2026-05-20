from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class EntityType(StrEnum):
    ADDRESS_OBJECT = "address_object"
    ADDRESS_GROUP = "address_group"
    SERVICE_OBJECT = "service_object"
    SERVICE_GROUP = "service_group"
    TAG = "tag"
    ZONE = "zone"
    SECURITY_RULE = "security_rule"
    NAT_RULE = "nat_rule"


class NormalizedEntity(BaseModel):
    name: str
    entity_type: EntityType
    scope_path: str
    metadata: dict[str, Any] = Field(default_factory=dict)
