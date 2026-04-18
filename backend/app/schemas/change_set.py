from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ChangeSetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    name: str
    description: str | None
    status: str
    created_at: datetime
    applied_at: datetime | None
    preview_summary: dict
    operations_payload: dict


class ChangeSetCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=4000)


class ChangeSetStatusUpdate(BaseModel):
    status: str


class NormalizationSelection(BaseModel):
    object_id: str
    kind: str


class MergePreviewRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=4000)
    selected_object_ids: list[str] = Field(default_factory=list)
    selected_normalizations: list[NormalizationSelection] = Field(default_factory=list)
