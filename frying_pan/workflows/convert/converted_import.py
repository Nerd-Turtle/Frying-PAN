from __future__ import annotations

from pydantic import BaseModel, Field

from frying_pan.normalized.config import NormalizedConfig
from frying_pan.normalized.vendor_metadata import ConversionWarning, UnsupportedFeature


class ConvertedImportPackage(BaseModel):
    name: str
    normalized_config: NormalizedConfig
    warnings: list[ConversionWarning] = Field(default_factory=list)
    unsupported_features: list[UnsupportedFeature] = Field(default_factory=list)
