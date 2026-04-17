import hashlib
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import get_settings


@dataclass(frozen=True)
class StoredUpload:
    filename: str
    label: str
    storage_path: str
    file_sha256: str


def ensure_storage_layout() -> None:
    settings = get_settings()
    root = Path(settings.storage_root)
    for path in (root, root / "uploads", root / "projects", root / "exports"):
        path.mkdir(parents=True, exist_ok=True)


def save_uploaded_source_file(project_id: str, upload: UploadFile) -> StoredUpload:
    settings = get_settings()
    original_name = Path(upload.filename or "source.xml").name
    destination_dir = Path(settings.storage_root) / "uploads" / project_id
    destination_dir.mkdir(parents=True, exist_ok=True)

    destination_name = f"{uuid4()}-{original_name}"
    destination_path = destination_dir / destination_name

    digest = hashlib.sha256()

    with destination_path.open("wb") as buffer:
        while chunk := upload.file.read(1024 * 1024):
            buffer.write(chunk)
            digest.update(chunk)

    upload.file.seek(0)

    return StoredUpload(
        filename=original_name,
        label=Path(original_name).stem or original_name,
        storage_path=str(destination_path),
        file_sha256=digest.hexdigest(),
    )


def delete_stored_file(storage_path: str) -> None:
    path = Path(storage_path)
    if path.exists():
        path.unlink()
