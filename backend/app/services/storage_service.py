import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import get_settings


def ensure_storage_layout() -> None:
    settings = get_settings()
    root = Path(settings.storage_root)
    for path in (root, root / "uploads", root / "projects", root / "exports"):
        path.mkdir(parents=True, exist_ok=True)


def save_uploaded_source_file(project_id: str, upload: UploadFile) -> str:
    settings = get_settings()
    original_name = Path(upload.filename or "source.xml").name
    destination_dir = Path(settings.storage_root) / "uploads" / project_id
    destination_dir.mkdir(parents=True, exist_ok=True)

    destination_name = f"{uuid4()}-{original_name}"
    destination_path = destination_dir / destination_name

    with destination_path.open("wb") as buffer:
        shutil.copyfileobj(upload.file, buffer)

    return str(destination_path)
