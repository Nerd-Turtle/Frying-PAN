from __future__ import annotations

from frying_pan.normalized.config import NormalizedConfig
from frying_pan.normalized.scope import ConfigScope, ScopeType
from frying_pan.sources.base import SourceAdapter, SourceConfig, SourceType


class PanoramaXmlAdapter(SourceAdapter):
    source_type = SourceType.PANORAMA_XML

    def parse(self, source: SourceConfig) -> NormalizedConfig:
        # TODO: Port useful parser research into dedicated PAN-OS normalizers.
        return NormalizedConfig(
            source_id=source.id,
            source_type=source.source_type,
            scopes=[ConfigScope(name="shared", scope_type=ScopeType.SHARED, path="shared")],
            warnings=["Panorama XML parser is scaffolded; full normalization is pending."],
        )
