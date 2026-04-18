from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SourceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    label: str
    filename: str
    storage_path: str
    file_sha256: str
    source_type: str
    parse_status: str
    imported_by_user_id: str | None
    imported_at: datetime


class EventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    actor_user_id: str | None
    event_type: str
    payload: str | None
    created_at: datetime
