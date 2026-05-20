from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from frying_pan.normalized.entity import EntityType, NormalizedEntity


class AddressKind(StrEnum):
    IP_NETMASK = "ip-netmask"
    IP_RANGE = "ip-range"
    FQDN = "fqdn"
    UNKNOWN = "unknown"


class AddressObject(NormalizedEntity):
    entity_type: EntityType = EntityType.ADDRESS_OBJECT
    address_kind: AddressKind = AddressKind.UNKNOWN
    value: str | None = None


class AddressGroup(NormalizedEntity):
    entity_type: EntityType = EntityType.ADDRESS_GROUP
    members: list[str] = Field(default_factory=list)
    dynamic_filter: str | None = None
