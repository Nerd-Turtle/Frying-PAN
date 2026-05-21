from __future__ import annotations

from pathlib import Path

from frying_pan.analysis.dependencies import build_dependency_map
from frying_pan.analysis.references import extract_references
from frying_pan.normalized.references import ReferenceKind
from frying_pan.sources.base import SourceConfig, SourceType
from frying_pan.sources.panorama_xml import PanoramaXmlAdapter

FIXTURES = Path(__file__).parent / "fixtures"


def test_dependency_resolver_scaffold_returns_empty_list() -> None:
    assert build_dependency_map() == []


def test_reference_extraction_records_rule_references() -> None:
    source_path = FIXTURES / "panorama" / "reference_config_items.xml"
    source = SourceConfig(
        display_name=source_path.name,
        original_path=source_path,
        source_type=SourceType.PANORAMA_XML,
    )
    config = PanoramaXmlAdapter().parse(source)

    references = extract_references(config)

    assert any(
        reference.owner_name == "FP-REF-PRE-ALLOW-HQ-TO-DMZ-WEB"
        and reference.target_name == "FP-REF-ADDR-HQ-USERS-10.10.10.0_24"
        and reference.reference_kind == ReferenceKind.RULE_SOURCE_ADDRESS
        and reference.resolved
        for reference in references
    )


def test_dependency_map_contains_resolved_and_unresolved_records() -> None:
    source_path = FIXTURES / "panorama" / "reference_config_items.xml"
    source = SourceConfig(
        display_name=source_path.name,
        original_path=source_path,
        source_type=SourceType.PANORAMA_XML,
    )
    config = PanoramaXmlAdapter().parse(source)

    dependencies = build_dependency_map(config)

    assert any(
        dependency.owner_name == "FP-REF-AG-STATIC-DMZ-SERVERS"
        and dependency.target_name == "FP-REF-ADDR-DMZ-WEB-10.20.10.10"
        and dependency.reference_kind == ReferenceKind.ADDRESS_GROUP_MEMBER
        and dependency.resolved
        for dependency in dependencies
    )
    assert any(
        dependency.owner_name == "FP-REF-PRE-ALLOW-HQ-TO-DMZ-WEB"
        and dependency.target_name == "web-browsing"
        and not dependency.resolved
        and dependency.warnings
        for dependency in dependencies
    )
