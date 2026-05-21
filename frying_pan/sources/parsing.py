from __future__ import annotations

from pathlib import Path

from frying_pan.normalized.config import NormalizedConfig
from frying_pan.sources.base import SourceConfig, SourceType
from frying_pan.sources.detection import checksum_sha256, detect_source
from frying_pan.sources.firewall_xml import FirewallXmlAdapter
from frying_pan.sources.panorama_xml import PanoramaXmlAdapter


class SourceParseError(ValueError):
    pass


def parse_source(path: Path) -> NormalizedConfig:
    detection = detect_source(path)
    if detection.source_type == SourceType.PANORAMA_XML:
        adapter = PanoramaXmlAdapter()
    elif detection.source_type == SourceType.FIREWALL_XML:
        adapter = FirewallXmlAdapter()
    else:
        warnings = (
            "; ".join(detection.warnings) if detection.warnings else "unsupported source type"
        )
        raise SourceParseError(f"Cannot parse {path}: {detection.source_type.value} ({warnings})")

    source = SourceConfig(
        display_name=path.name,
        original_path=path,
        checksum_sha256=checksum_sha256(path),
        source_type=detection.source_type,
        metadata=detection.model_dump(),
    )
    config = adapter.parse(source)
    config.warnings.extend(detection.warnings)
    return config
