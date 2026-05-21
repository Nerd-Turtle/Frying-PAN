from __future__ import annotations

from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, computed_field

from frying_pan.normalized.config import NormalizedConfig
from frying_pan.normalized.vendor_metadata import ConversionWarning, UnsupportedFeature


class ConversionPackageValidation(BaseModel):
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    @computed_field
    @property
    def valid(self) -> bool:
        return not self.errors


class ConvertedImportPackage(BaseModel):
    package_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    source_format: str = "generic-json"
    source_path: str | None = None
    source_metadata: dict[str, Any] = Field(default_factory=dict)
    normalized_config: NormalizedConfig
    warnings: list[ConversionWarning] = Field(default_factory=list)
    unsupported_features: list[UnsupportedFeature] = Field(default_factory=list)
    validation: ConversionPackageValidation = Field(default_factory=ConversionPackageValidation)

    @computed_field
    @property
    def scope_count(self) -> int:
        return len(self.normalized_config.scopes)

    @computed_field
    @property
    def entity_count(self) -> int:
        return len(self.normalized_config.entities)

    @computed_field
    @property
    def security_rule_count(self) -> int:
        return len(self.normalized_config.security_rules)

    @computed_field
    @property
    def warning_count(self) -> int:
        return len(self.warnings)

    @computed_field
    @property
    def unsupported_count(self) -> int:
        return len(self.unsupported_features)
