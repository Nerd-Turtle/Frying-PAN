from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.source import EventRead, SourceRead


class ProjectCollaboratorRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    username: str | None
    display_name: str | None
    role: str


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    visibility: Literal["public", "private"] = "public"
    contributor_usernames: list[str] = Field(default_factory=list)
    organization_id: str | None = None


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    visibility: Literal["public", "private"] | None = None
    contributor_usernames: list[str] | None = None


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str | None
    name: str
    description: str | None
    status: str
    visibility: str
    created_by_user_id: str | None
    created_by_display_name: str | None = None
    owner_user_id: str | None = None
    owner_display_name: str | None = None
    collaborators: list[ProjectCollaboratorRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class ProjectDetail(ProjectRead):
    sources: list[SourceRead] = Field(default_factory=list)
    events: list[EventRead] = Field(default_factory=list)


class PlaceholderActionResponse(BaseModel):
    status: str
    message: str
