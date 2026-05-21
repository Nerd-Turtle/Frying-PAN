from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class ReferenceKind(StrEnum):
    ADDRESS_GROUP_MEMBER = "address_group_member"
    SERVICE_GROUP_MEMBER = "service_group_member"
    RULE_SOURCE_ZONE = "rule_source_zone"
    RULE_DESTINATION_ZONE = "rule_destination_zone"
    RULE_SOURCE_ADDRESS = "rule_source_address"
    RULE_DESTINATION_ADDRESS = "rule_destination_address"
    RULE_APPLICATION = "rule_application"
    RULE_SERVICE = "rule_service"
    RULE_URL_CATEGORY = "rule_url_category"
    RULE_PROFILE_GROUP = "rule_profile_group"
    TAG = "tag"


class Reference(BaseModel):
    owner_scope_path: str
    owner_name: str
    owner_type: str
    target_name: str
    reference_kind: ReferenceKind
    target_type_hints: list[str] = Field(default_factory=list)
    scope_context: str | None = None
    resolved: bool = False
    warnings: list[str] = Field(default_factory=list)


class Dependency(BaseModel):
    owner_scope_path: str
    owner_name: str
    owner_type: str
    target_name: str
    reference_kind: ReferenceKind | None = None
    target_type_hints: list[str] = Field(default_factory=list)
    scope_context: str | None = None
    resolved: bool = False
    warnings: list[str] = Field(default_factory=list)


class Conflict(BaseModel):
    conflict_type: str
    source_paths: list[str]
    explanation: str
    recommendation: str | None = None
