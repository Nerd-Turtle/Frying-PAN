from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class SourceType(StrEnum):
    PANORAMA_XML = "panorama_xml"
    FIREWALL_XML = "firewall_xml"
    UNKNOWN_PANOS_XML = "unknown_panos_xml"
    VENDOR_IMPORT_FUTURE = "vendor_import_future"
    NORMALIZED_IMPORT_FUTURE = "normalized_import_future"
    UNKNOWN = "unknown"


class SourceDetectionResult(BaseModel):
    source_type: SourceType
    panos_version: str | None = None
    supports_device_groups: bool = False
    has_vsys: bool = False
    has_templates: bool = False
    has_template_stacks: bool = False
    warnings: list[str] = Field(default_factory=list)


class SourceConfig(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    display_name: str
    original_path: Path
    workspace_path: Path | None = None
    checksum_sha256: str | None = None
    source_type: SourceType = SourceType.UNKNOWN
    imported_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = Field(default_factory=dict)


class SourceAdapter(ABC):
    source_type: SourceType

    @abstractmethod
    def parse(self, source: SourceConfig):
        """Parse a source into a normalized config model."""
