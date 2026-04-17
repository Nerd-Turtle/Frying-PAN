from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AnalysisFilters(BaseModel):
    source_id: str | None = None
    object_type: str | None = None
    scope_path: str | None = None


class AnalysisObjectRef(BaseModel):
    id: str
    source_id: str
    scope_path: str
    object_type: str
    object_name: str
    normalized_hash: str | None
    raw_payload: dict
    normalized_payload: dict


class DuplicateFinding(BaseModel):
    finding_kind: str
    object_type: str
    key: str
    normalized_payload: dict | None = None
    items: list[AnalysisObjectRef] = Field(default_factory=list)


class NormalizationSuggestion(BaseModel):
    object_id: str
    source_id: str
    scope_path: str
    object_type: str
    object_name: str
    kind: str
    original_value: str
    suggested_value: str


class PromotionAssessment(BaseModel):
    object_id: str
    source_id: str
    scope_path: str
    object_type: str
    object_name: str
    status: str
    blockers: list[str] = Field(default_factory=list)
    dependency_targets: list[str] = Field(default_factory=list)
    mixed_scope_dependencies: bool = False
    notes: list[str] = Field(default_factory=list)


class ProjectAnalysisReport(BaseModel):
    generated_at: datetime
    filters: AnalysisFilters
    duplicate_name_findings: list[DuplicateFinding] = Field(default_factory=list)
    duplicate_value_findings: list[DuplicateFinding] = Field(default_factory=list)
    normalization_suggestions: list[NormalizationSuggestion] = Field(default_factory=list)
    promotion_candidates: list[PromotionAssessment] = Field(default_factory=list)
    promotion_blockers: list[PromotionAssessment] = Field(default_factory=list)


class AnalysisRunResponse(BaseModel):
    status: str
    message: str
    report: ProjectAnalysisReport
