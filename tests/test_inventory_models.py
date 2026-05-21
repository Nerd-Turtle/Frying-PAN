from __future__ import annotations

from pathlib import Path

from frying_pan.normalized.addresses import AddressGroup, AddressKind, AddressObject
from frying_pan.normalized.config import NormalizedConfig
from frying_pan.normalized.objects import Tag
from frying_pan.normalized.references import Dependency, Reference, ReferenceKind
from frying_pan.normalized.rules import RuleAction, Rulebase, RulebaseType, SecurityRule
from frying_pan.normalized.scope import ConfigScope, ScopeType
from frying_pan.normalized.services import Protocol, ServiceGroup, ServiceObject, ServicePort
from frying_pan.sources.base import SourceConfig, SourceType
from frying_pan.sources.firewall_xml import FirewallXmlAdapter
from frying_pan.sources.panorama_xml import PanoramaXmlAdapter

FIXTURES = Path(__file__).parent / "fixtures"


def test_phase_1_inventory_models_can_be_instantiated() -> None:
    source = SourceConfig(
        display_name="source.xml",
        original_path=Path("source.xml"),
        source_type=SourceType.PANORAMA_XML,
    )
    scope = ConfigScope(name="shared", scope_type=ScopeType.SHARED, path="shared")
    address = AddressObject(
        name="addr",
        scope_path="shared",
        address_kind=AddressKind.IP_NETMASK,
        value="192.0.2.10",
    )
    address_group = AddressGroup(name="ag", scope_path="shared", members=["addr"])
    service = ServiceObject(
        name="svc",
        scope_path="shared",
        ports=[ServicePort(protocol=Protocol.TCP, destination="443")],
    )
    service_group = ServiceGroup(name="sg", scope_path="shared", members=["svc"])
    tag = Tag(name="tag", scope_path="shared", color="color1")
    rule = SecurityRule(
        name="allow",
        scope_path="shared",
        rulebase_type=RulebaseType.SECURITY_PRE,
        position=1,
        action=RuleAction.ALLOW,
    )
    rulebase = Rulebase(
        scope_path="shared",
        rulebase_type=RulebaseType.SECURITY_PRE,
        security_rules=[rule],
    )
    reference = Reference(
        owner_scope_path="shared",
        owner_name="ag",
        owner_type="address_group",
        target_name="addr",
        reference_kind=ReferenceKind.ADDRESS_GROUP_MEMBER,
        resolved=True,
    )
    dependency = Dependency(
        owner_scope_path="shared",
        owner_name="ag",
        owner_type="address_group",
        target_name="addr",
        reference_kind=ReferenceKind.ADDRESS_GROUP_MEMBER,
        resolved=True,
    )
    config = NormalizedConfig(
        source_id=source.id,
        source_type=source.source_type,
        scopes=[scope],
        entities=[address, address_group, service, service_group, tag],
        rulebases=[rulebase],
        security_rules=[rule],
        references=[reference],
        dependencies=[dependency],
    )

    assert config.source_id == source.id
    assert config.rulebases[0].security_rules[0].name == "allow"
    assert config.references[0].reference_kind == ReferenceKind.ADDRESS_GROUP_MEMBER


def test_parsed_panorama_and_firewall_configs_use_normalized_models() -> None:
    panorama_source = SourceConfig(
        display_name="reference_config_items.xml",
        original_path=FIXTURES / "panorama" / "reference_config_items.xml",
        source_type=SourceType.PANORAMA_XML,
    )
    firewall_source = SourceConfig(
        display_name="reference_config_items_virtual_router.xml",
        original_path=FIXTURES / "firewall" / "reference_config_items_virtual_router.xml",
        source_type=SourceType.FIREWALL_XML,
    )

    panorama_config = PanoramaXmlAdapter().parse(panorama_source)
    firewall_config = FirewallXmlAdapter().parse(firewall_source)

    assert panorama_config.entities
    assert firewall_config.entities
    assert panorama_config.rulebases
    assert firewall_config.rulebases
    assert panorama_config.references
    assert firewall_config.dependencies
    assert panorama_config.entities[0].metadata["source_id"] == panorama_source.id
    assert firewall_config.security_rules[0].metadata["source_type"] == SourceType.FIREWALL_XML
