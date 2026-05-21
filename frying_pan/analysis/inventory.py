from __future__ import annotations

from pydantic import BaseModel, Field

from frying_pan.normalized.config import NormalizedConfig


class InventorySummary(BaseModel):
    source_id: str
    source_type: str
    scope_count: int
    entity_count: int
    security_rule_count: int
    reference_count: int = 0
    dependency_count: int = 0
    unresolved_reference_count: int = 0
    warning_count: int
    entity_counts_by_type: dict[str, int] = Field(default_factory=dict)
    security_rule_counts_by_rulebase: dict[str, int] = Field(default_factory=dict)
    scopes: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


def summarize_inventory(config: NormalizedConfig) -> InventorySummary:
    return InventorySummary(
        source_id=config.source_id,
        source_type=config.source_type.value,
        scope_count=len(config.scopes),
        entity_count=len(config.entities),
        security_rule_count=len(config.security_rules),
        reference_count=len(config.references),
        dependency_count=len(config.dependencies),
        unresolved_reference_count=sum(
            1 for reference in config.references if not reference.resolved
        ),
        warning_count=len(config.warnings),
        entity_counts_by_type=_entity_counts_by_type(config),
        security_rule_counts_by_rulebase=_security_rule_counts_by_rulebase(config),
        scopes=[f"{scope.scope_type.value}:{scope.name}" for scope in config.scopes],
        warnings=config.warnings,
    )


def _entity_counts_by_type(config: NormalizedConfig) -> dict[str, int]:
    counts: dict[str, int] = {}
    for entity in config.entities:
        counts[entity.entity_type.value] = counts.get(entity.entity_type.value, 0) + 1
    return counts


def _security_rule_counts_by_rulebase(config: NormalizedConfig) -> dict[str, int]:
    counts: dict[str, int] = {}
    for rule in config.security_rules:
        counts[rule.rulebase_type.value] = counts.get(rule.rulebase_type.value, 0) + 1
    return counts
