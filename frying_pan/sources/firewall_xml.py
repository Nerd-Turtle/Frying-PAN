from __future__ import annotations

from frying_pan.normalized.config import NormalizedConfig
from frying_pan.normalized.scope import ConfigScope, ScopeType
from frying_pan.sources.base import SourceAdapter, SourceConfig, SourceType


class FirewallXmlAdapter(SourceAdapter):
    source_type = SourceType.FIREWALL_XML

    def parse(self, source: SourceConfig) -> NormalizedConfig:
        # TODO: Detect vsys scopes and normalize local objects/rulebases.
        return NormalizedConfig(
            source_id=source.id,
            source_type=source.source_type,
            scopes=[ConfigScope(name="local", scope_type=ScopeType.VSYS, path="local")],
            warnings=["Firewall XML parser is scaffolded; full normalization is pending."],
        )
