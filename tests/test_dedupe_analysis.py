from __future__ import annotations

from frying_pan.analysis.conflicts import detect_conflicts
from frying_pan.analysis.dedupe import (
    DedupeAnalysisEngine,
    find_duplicate_objects,
    fingerprint_entity,
)
from frying_pan.analysis.dedupe_models import DedupeFindingType
from frying_pan.analysis.unused import find_unused_candidates
from frying_pan.normalized.addresses import AddressGroup, AddressKind, AddressObject
from frying_pan.normalized.config import NormalizedConfig
from frying_pan.normalized.references import Reference, ReferenceKind
from frying_pan.normalized.scope import ConfigScope, ScopeType
from frying_pan.normalized.services import Protocol, ServiceGroup, ServiceObject, ServicePort
from frying_pan.sources.base import SourceType


def test_fingerprint_normalizes_equivalent_address_objects() -> None:
    left = AddressObject(
        name="a",
        scope_path="shared",
        address_kind=AddressKind.IP_NETMASK,
        value="192.0.2.10/32",
    )
    right = AddressObject(
        name="b",
        scope_path="device-group/DG-A",
        address_kind=AddressKind.IP_NETMASK,
        value="192.0.2.10",
    )

    assert fingerprint_entity(left).fingerprint == fingerprint_entity(right).fingerprint


def test_dedupe_analysis_finds_duplicates_conflicts_unused_and_placement() -> None:
    config = _config(
        [
            AddressObject(
                name="shared-host",
                scope_path="device-group/DG-A",
                address_kind=AddressKind.IP_NETMASK,
                value="192.0.2.10",
            ),
            AddressObject(
                name="other-host",
                scope_path="device-group/DG-B",
                address_kind=AddressKind.IP_NETMASK,
                value="192.0.2.10/32",
            ),
            AddressObject(
                name="override-me",
                scope_path="shared",
                address_kind=AddressKind.IP_NETMASK,
                value="198.51.100.10",
            ),
            AddressObject(
                name="override-me",
                scope_path="device-group/DG-A",
                address_kind=AddressKind.IP_NETMASK,
                value="198.51.100.20",
            ),
            AddressObject(
                name="used-host",
                scope_path="shared",
                address_kind=AddressKind.IP_NETMASK,
                value="203.0.113.10",
            ),
        ],
        references=[
            Reference(
                owner_scope_path="device-group/DG-A",
                owner_name="rule-1",
                owner_type="security_rule",
                target_name="used-host",
                reference_kind=ReferenceKind.RULE_SOURCE_ADDRESS,
                resolved=True,
            )
        ],
    )

    result = DedupeAnalysisEngine().analyze(config)
    finding_types = {finding.finding_type for finding in result.findings}

    assert DedupeFindingType.DUPLICATE_OBJECT in finding_types
    assert DedupeFindingType.SAME_NAME_CONFLICT in finding_types
    assert DedupeFindingType.UNUSED_OBJECT_CANDIDATE in finding_types
    assert DedupeFindingType.PLACEMENT_RECOMMENDATION in finding_types
    assert "used-host" not in {
        name
        for finding in result.findings
        if finding.finding_type == DedupeFindingType.UNUSED_OBJECT_CANDIDATE
        for name in finding.object_names
    }


def test_dedupe_analysis_warns_for_dynamic_address_group_and_bad_service_port() -> None:
    config = _config(
        [
            AddressGroup(
                name="dynamic-group",
                scope_path="shared",
                dynamic_filter="'tag-a'",
            ),
            ServiceObject(
                name="bad-service",
                scope_path="shared",
                ports=[ServicePort(protocol=Protocol.TCP, destination="not-a-port")],
            ),
            ServiceGroup(name="sg", scope_path="shared", members=["bad-service"]),
        ]
    )

    result = DedupeAnalysisEngine().analyze(config)

    assert any(
        finding.finding_type == DedupeFindingType.UNSUPPORTED_OBJECT
        for finding in result.findings
    )


def test_compatibility_wrappers_return_filtered_findings() -> None:
    config = _config(
        [
            AddressObject(
                name="a",
                scope_path="shared",
                address_kind=AddressKind.IP_NETMASK,
                value="192.0.2.10",
            ),
            AddressObject(
                name="b",
                scope_path="device-group/DG-A",
                address_kind=AddressKind.IP_NETMASK,
                value="192.0.2.10",
            ),
        ]
    )

    assert find_duplicate_objects(config)
    assert find_unused_candidates(config)
    assert detect_conflicts(config) == []


def _config(entities, references=None):
    return NormalizedConfig(
        source_id="source-1",
        source_type=SourceType.PANORAMA_XML,
        scopes=[
            ConfigScope(name="shared", scope_type=ScopeType.SHARED, path="shared"),
            ConfigScope(
                name="DG-A",
                scope_type=ScopeType.DEVICE_GROUP,
                path="device-group/DG-A",
            ),
            ConfigScope(
                name="DG-B",
                scope_type=ScopeType.DEVICE_GROUP,
                path="device-group/DG-B",
            ),
        ],
        entities=entities,
        references=references or [],
    )
