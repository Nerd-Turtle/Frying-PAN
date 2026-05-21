from __future__ import annotations

from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, computed_field

from frying_pan.policy.assurance.behavior_diff import BehaviorDiff
from frying_pan.workflows.migrate.object_mapping import ObjectMapping
from frying_pan.workflows.migrate.rule_mapping import RuleMapping
from frying_pan.workflows.migrate.scope_mapping import ScopeMapping, ZoneMapping


class MigrationAction(StrEnum):
    COPY_OBJECT = "copy_object"
    MAP_OBJECT = "map_object"
    MAP_SCOPE = "map_scope"
    MAP_ZONE = "map_zone"
    COPY_RULE = "copy_rule"
    PLACE_RULE = "place_rule"
    INCLUDE_DEPENDENCY = "include_dependency"
    SKIP = "skip"


class MigrationPlanStatus(StrEnum):
    DRAFT = "draft"
    READY_FOR_REVIEW = "ready_for_review"
    BLOCKED = "blocked"


class MigrationDecisionStatus(StrEnum):
    STAGED = "staged"
    BLOCKED = "blocked"
    APPROVED = "approved"


class MigrationValidationLevel(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class MigrationValidationMessage(BaseModel):
    level: MigrationValidationLevel
    message: str
    decision_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class MigrationValidation(BaseModel):
    messages: list[MigrationValidationMessage] = Field(default_factory=list)

    @computed_field
    @property
    def has_errors(self) -> bool:
        return any(message.level == MigrationValidationLevel.ERROR for message in self.messages)

    @computed_field
    @property
    def has_warnings(self) -> bool:
        return any(message.level == MigrationValidationLevel.WARNING for message in self.messages)


class PlanDecision(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    action: MigrationAction
    source_ref: str
    target_ref: str | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    approved: bool = False
    status: MigrationDecisionStatus = MigrationDecisionStatus.STAGED


class MigrationPlanPreview(BaseModel):
    source_config_ids: list[str]
    target_config_id: str
    decision_summaries: list[str] = Field(default_factory=list)
    dependency_summaries: list[str] = Field(default_factory=list)
    assurance_summaries: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    export_blocked: bool = True


class MigrationPlan(BaseModel):
    source_config_ids: list[str]
    target_config_id: str
    source_type: str | None = None
    target_type: str | None = None
    status: MigrationPlanStatus = MigrationPlanStatus.DRAFT
    scope_mappings: list[ScopeMapping] = Field(default_factory=list)
    zone_mappings: list[ZoneMapping] = Field(default_factory=list)
    object_mappings: list[ObjectMapping] = Field(default_factory=list)
    rule_mappings: list[RuleMapping] = Field(default_factory=list)
    decisions: list[PlanDecision] = Field(default_factory=list)
    dependency_refs: list[str] = Field(default_factory=list)
    assurance_results: list[BehaviorDiff] = Field(default_factory=list)
    validation: MigrationValidation = Field(default_factory=MigrationValidation)
    warnings: list[str] = Field(default_factory=list)
    assurance_required: bool = True

    @computed_field
    @property
    def decision_count(self) -> int:
        return len(self.decisions)

    @computed_field
    @property
    def mapping_count(self) -> int:
        return (
            len(self.scope_mappings)
            + len(self.zone_mappings)
            + len(self.object_mappings)
            + len(self.rule_mappings)
        )
