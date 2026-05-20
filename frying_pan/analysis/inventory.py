from __future__ import annotations

from pydantic import BaseModel

from frying_pan.normalized.config import NormalizedConfig


class InventorySummary(BaseModel):
    scope_count: int
    entity_count: int
    security_rule_count: int
    warning_count: int


def summarize_inventory(config: NormalizedConfig) -> InventorySummary:
    return InventorySummary(
        scope_count=len(config.scopes),
        entity_count=len(config.entities),
        security_rule_count=len(config.security_rules),
        warning_count=len(config.warnings),
    )
