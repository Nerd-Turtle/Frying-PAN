from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.source import EventRead, SourceRead


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None
    status: str
    created_at: datetime
    updated_at: datetime


class ProjectDetail(ProjectRead):
    sources: list[SourceRead] = Field(default_factory=list)
    events: list[EventRead] = Field(default_factory=list)


class PlaceholderActionResponse(BaseModel):
    status: str
    message: str
