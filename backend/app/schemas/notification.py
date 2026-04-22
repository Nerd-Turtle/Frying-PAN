from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class NotificationSettingsRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    notification_timeout_seconds: int


class NotificationSettingsUpdateRequest(BaseModel):
    notification_timeout_seconds: int = Field(ge=3, le=60)


class NotificationHistoryEntryRead(BaseModel):
    id: str
    event_type: str
    payload: str | None
    actor_display_name: str | None
    project_name: str | None
    created_at: datetime


class AuditLogEntryRead(BaseModel):
    id: str
    source: str
    event_type: str
    payload: str | None
    actor_display_name: str | None
    project_name: str | None
    created_at: datetime
