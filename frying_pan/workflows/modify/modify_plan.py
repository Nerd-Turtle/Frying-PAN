from __future__ import annotations

from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, computed_field, model_validator


class ModifyAction(StrEnum):
    RENAME_OBJECT = "rename_object"
    MOVE_OBJECT = "move_object"
    DEDUPE_OBJECT = "dedupe_object"
    CLEAN_UNUSED_OBJECT = "clean_unused_object"
    REORDER_RULE = "reorder_rule"
    SET_RULE_ENABLED = "set_rule_enabled"
    SET_RULE_LOGGING = "set_rule_logging"


class ModifyPlanStatus(StrEnum):
    DRAFT = "draft"
    NEEDS_REVIEW = "needs_review"
    READY_FOR_REVIEW = "ready_for_review"
    BLOCKED = "blocked"


class ModifyActionStatus(StrEnum):
    STAGED = "staged"
    BLOCKED = "blocked"
    APPROVED = "approved"


class ValidationLevel(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class ModifyValidationMessage(BaseModel):
    level: ValidationLevel
    message: str
    action_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ModifyPlanValidation(BaseModel):
    messages: list[ModifyValidationMessage] = Field(default_factory=list)

    @computed_field
    @property
    def has_errors(self) -> bool:
        return any(message.level == ValidationLevel.ERROR for message in self.messages)

    @computed_field
    @property
    def has_warnings(self) -> bool:
        return any(message.level == ValidationLevel.WARNING for message in self.messages)


class ModifyPlanDecision(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    action: ModifyAction
    source_ref: str
    target_ref: str | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)
    impacted_references: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    approved: bool = False
    status: ModifyActionStatus = ModifyActionStatus.STAGED

    @model_validator(mode="after")
    def _validate_action_shape(self) -> ModifyPlanDecision:
        if self.action in {
            ModifyAction.RENAME_OBJECT,
            ModifyAction.MOVE_OBJECT,
            ModifyAction.DEDUPE_OBJECT,
        } and not self.target_ref:
            raise ValueError(f"{self.action.value} requires target_ref.")
        if self.action == ModifyAction.REORDER_RULE and "new_position" not in self.parameters:
            raise ValueError("reorder_rule requires parameters.new_position.")
        return self


class ModificationPlan(BaseModel):
    source_config_id: str
    source_type: str | None = None
    status: ModifyPlanStatus = ModifyPlanStatus.DRAFT
    decisions: list[ModifyPlanDecision] = Field(default_factory=list)
    validation: ModifyPlanValidation = Field(default_factory=ModifyPlanValidation)
    warnings: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)

    @computed_field
    @property
    def action_count(self) -> int:
        return len(self.decisions)

    @computed_field
    @property
    def approved_action_count(self) -> int:
        return sum(1 for decision in self.decisions if decision.approved)
