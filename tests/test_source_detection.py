from __future__ import annotations

from pathlib import Path

from frying_pan.sources.base import SourceType
from frying_pan.sources.detection import detect_source

FIXTURES = Path(__file__).parent / "fixtures"


def test_detects_panorama_xml() -> None:
    result = detect_source(FIXTURES / "panorama" / "basic_panorama.xml")

    assert result.source_type == SourceType.PANORAMA_XML
    assert result.panos_version == "11.1.0"
    assert result.has_shared_scope is True
    assert result.supports_device_groups is True
    assert result.has_vsys is False
    assert result.has_templates is True
    assert result.has_template_stacks is True


def test_detects_firewall_xml() -> None:
    result = detect_source(FIXTURES / "firewall" / "basic_firewall.xml")

    assert result.source_type == SourceType.FIREWALL_XML
    assert result.panos_version == "11.1.0"
    assert result.has_shared_scope is False
    assert result.has_vsys is True


def test_detects_unknown_panos_xml_with_warning() -> None:
    result = detect_source(FIXTURES / "unknown" / "unknown_panos.xml")

    assert result.source_type == SourceType.UNKNOWN_PANOS_XML
    assert result.panos_version == "11.1.0"
    assert result.has_shared_scope is True
    assert result.supports_device_groups is False
    assert result.has_vsys is False
    assert result.warnings == [
        "PAN-OS XML was detected, but this pass could not identify Panorama or firewall layout."
    ]


def test_invalid_xml_returns_useful_warning() -> None:
    result = detect_source(FIXTURES / "invalid" / "broken.xml")

    assert result.source_type == SourceType.UNKNOWN
    assert result.warnings
    assert "Source could not be parsed as XML" in result.warnings[0]
