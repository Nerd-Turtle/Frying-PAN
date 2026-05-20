from __future__ import annotations

import json
import shutil
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from pydantic import BaseModel, Field

from frying_pan.sources.base import SourceConfig
from frying_pan.sources.detection import checksum_sha256, detect_source

MANIFEST_NAME = "frying-pan.project.json"


class ProjectManifest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    sources: list[SourceConfig] = Field(default_factory=list)


class ProjectWorkspace(BaseModel):
    root: Path
    manifest: ProjectManifest

    @property
    def manifest_path(self) -> Path:
        return self.root / MANIFEST_NAME

    @property
    def sources_dir(self) -> Path:
        return self.root / "sources"

    @property
    def cache_dir(self) -> Path:
        return self.root / "cache"

    @property
    def exports_dir(self) -> Path:
        return self.root / "exports"

    @property
    def logs_dir(self) -> Path:
        return self.root / "logs"

    @classmethod
    def create(cls, root: Path, name: str) -> ProjectWorkspace:
        root.mkdir(parents=True, exist_ok=True)
        workspace = cls(root=root, manifest=ProjectManifest(name=name))
        workspace.ensure_layout()
        workspace.save()
        return workspace

    @classmethod
    def open(cls, root: Path) -> ProjectWorkspace:
        payload = json.loads((root / MANIFEST_NAME).read_text(encoding="utf-8"))
        workspace = cls(root=root, manifest=ProjectManifest.model_validate(payload))
        workspace.ensure_layout()
        return workspace

    def ensure_layout(self) -> None:
        for path in (self.sources_dir, self.cache_dir, self.exports_dir, self.logs_dir):
            path.mkdir(parents=True, exist_ok=True)

    def save(self) -> None:
        self.manifest.updated_at = datetime.now(UTC)
        self.manifest_path.write_text(self.manifest.model_dump_json(indent=2), encoding="utf-8")

    def import_source(self, source_path: Path) -> SourceConfig:
        detection = detect_source(source_path)
        digest = checksum_sha256(source_path)
        target_path = self.sources_dir / source_path.name
        if source_path.resolve() != target_path.resolve():
            shutil.copy2(source_path, target_path)
        source = SourceConfig(
            display_name=source_path.name,
            original_path=source_path,
            workspace_path=target_path,
            checksum_sha256=digest,
            source_type=detection.source_type,
            metadata=detection.model_dump(),
        )
        self.manifest.sources.append(source)
        self.save()
        return source
