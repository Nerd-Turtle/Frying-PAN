from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from frying_pan.normalized.entity import EntityType, NormalizedEntity


class RuleAction(StrEnum):
    ALLOW = "allow"
    DENY = "deny"
    DROP = "drop"
    RESET_CLIENT = "reset-client"
    RESET_SERVER = "reset-server"
    RESET_BOTH = "reset-both"
    UNKNOWN = "unknown"


class RulebaseType(StrEnum):
    SECURITY_PRE = "security_pre"
    SECURITY_POST = "security_post"
    SECURITY_LOCAL = "security_local"
    NAT = "nat"


class SecurityRule(NormalizedEntity):
    entity_type: EntityType = EntityType.SECURITY_RULE
    rulebase_type: RulebaseType = RulebaseType.SECURITY_LOCAL
    position: int = 0
    source_zones: list[str] = Field(default_factory=lambda: ["any"])
    destination_zones: list[str] = Field(default_factory=lambda: ["any"])
    source_addresses: list[str] = Field(default_factory=lambda: ["any"])
    destination_addresses: list[str] = Field(default_factory=lambda: ["any"])
    applications: list[str] = Field(default_factory=lambda: ["any"])
    services: list[str] = Field(default_factory=lambda: ["any"])
    users: list[str] = Field(default_factory=lambda: ["any"])
    url_categories: list[str] = Field(default_factory=list)
    action: RuleAction = RuleAction.UNKNOWN
    security_profiles: dict[str, str] = Field(default_factory=dict)


class NATRule(NormalizedEntity):
    entity_type: EntityType = EntityType.NAT_RULE
    position: int = 0
