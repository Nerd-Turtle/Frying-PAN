from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, computed_field


class DedupeFindingType(StrEnum):
    DUPLICATE_OBJECT = "duplicate_object"
    SAME_NAME_CONFLICT = "same_name_conflict"
    UNUSED_OBJECT_CANDIDATE = "unused_object_candidate"
    PLACEMENT_RECOMMENDATION = "placement_recommendation"
    UNSUPPORTED_OBJECT = "unsupported_object"


class DedupeSeverity(StrEnum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ObjectFingerprint(BaseModel):
    entity_type: str
    fingerprint: str
    comparable: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)


class DedupeFinding(BaseModel):
    finding_id: str | None = None
    finding_type: DedupeFindingType
    severity: DedupeSeverity
    object_type: str
    object_names: list[str] = Field(default_factory=list)
    scopes: list[str] = Field(default_factory=list)
    fingerprints: list[str] = Field(default_factory=list)
    explanation: str
    recommendation: str | None = None
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class DedupeAnalysisResult(BaseModel):
    source_id: str
    source_type: str | None = None
    analyzed_object_count: int = 0
    findings: list[DedupeFinding] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    @computed_field
    @property
    def finding_count(self) -> int:
        return len(self.findings)

    @computed_field
    @property
    def finding_counts_by_type(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for finding in self.findings:
            counts[finding.finding_type.value] = counts.get(finding.finding_type.value, 0) + 1
        return counts

    @computed_field
    @property
    def finding_counts_by_severity(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for finding in self.findings:
            counts[finding.severity.value] = counts.get(finding.severity.value, 0) + 1
        return counts
