from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class FindingType(StrEnum):
    FULL_SHADOW = "FULL_SHADOW"
    PARTIAL_SHADOW = "PARTIAL_SHADOW"
    REDUNDANT_RULE = "REDUNDANT_RULE"
    DUPLICATE_RULE = "DUPLICATE_RULE"
    BROAD_ALLOW = "BROAD_ALLOW"
    BROAD_DENY = "BROAD_DENY"
    UNUSED_RULE_CANDIDATE = "UNUSED_RULE_CANDIDATE"
    PORT_BASED_ALLOW = "PORT_BASED_ALLOW"
    APP_ID_GAP = "APP_ID_GAP"
    SERVICE_APP_MISMATCH = "SERVICE_APP_MISMATCH"
    RULE_ORDER_RISK = "RULE_ORDER_RISK"
    MIGRATION_BEHAVIOR_CHANGED_ALLOW_TO_DENY = "MIGRATION_BEHAVIOR_CHANGED_ALLOW_TO_DENY"
    MIGRATION_BEHAVIOR_CHANGED_DENY_TO_ALLOW = "MIGRATION_BEHAVIOR_CHANGED_DENY_TO_ALLOW"
    MISSING_OBJECT_REFERENCE = "MISSING_OBJECT_REFERENCE"
    UNRESOLVED_APPLICATION = "UNRESOLVED_APPLICATION"
    UNSUPPORTED_MATCH_CRITERIA = "UNSUPPORTED_MATCH_CRITERIA"


class Severity(StrEnum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuditFinding(BaseModel):
    finding_type: FindingType
    severity: Severity
    source_config: str
    scope_or_rulebase: str
    affected_rules: list[str] = Field(default_factory=list)
    explanation: str
    affected_match_criteria: dict[str, str] = Field(default_factory=dict)
    recommendation: str | None = None
    confidence: str = "medium"
    warnings: list[str] = Field(default_factory=list)
