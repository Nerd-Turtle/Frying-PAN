from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ExportRequest(BaseModel):
    change_set_id: str | None = None


class ExportRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    change_set_id: str | None
    filename: str
    storage_path: str
    file_sha256: str
    export_status: str
    metadata_json: dict
    created_at: datetime
