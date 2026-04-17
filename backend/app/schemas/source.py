from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SourceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    storage_path: str
    kind: str
    parse_status: str
    uploaded_at: datetime


class EventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    event_type: str
    payload: str | None
    created_at: datetime
