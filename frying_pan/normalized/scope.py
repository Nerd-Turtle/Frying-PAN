from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class ScopeType(StrEnum):
    SHARED = "shared"
    DEVICE_GROUP = "device_group"
    TEMPLATE = "template"
    TEMPLATE_STACK = "template_stack"
    VSYS = "vsys"
    SYNTHETIC_VENDOR = "synthetic_vendor"


class ConfigScope(BaseModel):
    name: str
    scope_type: ScopeType
    path: str
    parent_path: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)
