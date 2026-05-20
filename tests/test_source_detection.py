from __future__ import annotations

from pathlib import Path

from frying_pan.sources.base import SourceType
from frying_pan.sources.detection import detect_source

FIXTURES = Path(__file__).parent / "fixtures"


def test_detects_panorama_xml() -> None:
    result = detect_source(FIXTURES / "panorama" / "basic_panorama.xml")

    assert result.source_type == SourceType.PANORAMA_XML
    assert result.supports_device_groups is True
    assert result.has_templates is True
    assert result.has_template_stacks is True


def test_detects_firewall_xml() -> None:
    result = detect_source(FIXTURES / "firewall" / "basic_firewall.xml")

    assert result.source_type == SourceType.FIREWALL_XML
    assert result.has_vsys is True
