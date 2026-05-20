from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

from frying_pan.normalized.entity import EntityType, NormalizedEntity


class Protocol(StrEnum):
    TCP = "tcp"
    UDP = "udp"
    UNKNOWN = "unknown"


class ServicePort(BaseModel):
    protocol: Protocol
    destination: str
    source: str | None = None


class ServiceObject(NormalizedEntity):
    entity_type: EntityType = EntityType.SERVICE_OBJECT
    ports: list[ServicePort] = Field(default_factory=list)


class ServiceGroup(NormalizedEntity):
    entity_type: EntityType = EntityType.SERVICE_GROUP
    members: list[str] = Field(default_factory=list)
