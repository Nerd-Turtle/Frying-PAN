from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, computed_field


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
    DISABLED_RULE = "DISABLED_RULE"
    LOGGING_GAP = "LOGGING_GAP"
    CLEANUP_RULE = "CLEANUP_RULE"
    MISSING_CLEANUP = "MISSING_CLEANUP"
    APPLICATION_DEFAULT_REVIEW = "APPLICATION_DEFAULT_REVIEW"


class Severity(StrEnum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuditFinding(BaseModel):
    finding_id: str | None = None
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
    metadata: dict[str, Any] = Field(default_factory=dict)


class PolicyAuditResult(BaseModel):
    source_id: str
    source_type: str | None = None
    scope_path: str | None = None
    audited_rule_count: int = 0
    findings: list[AuditFinding] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    @computed_field
    @property
    def finding_count(self) -> int:
        return len(self.findings)

    @computed_field
    @property
    def finding_counts_by_type(self) -> dict[str, int]:
        return self.counts_by_type()

    @computed_field
    @property
    def finding_counts_by_severity(self) -> dict[str, int]:
        return self.counts_by_severity()

    def counts_by_type(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for finding in self.findings:
            counts[finding.finding_type.value] = counts.get(finding.finding_type.value, 0) + 1
        return counts

    def counts_by_severity(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for finding in self.findings:
            counts[finding.severity.value] = counts.get(finding.severity.value, 0) + 1
        return counts
