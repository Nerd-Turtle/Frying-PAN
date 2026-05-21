from __future__ import annotations

from pathlib import Path

from frying_pan.normalized.addresses import AddressGroup, AddressKind, AddressObject
from frying_pan.normalized.entity import EntityType
from frying_pan.normalized.objects import Tag
from frying_pan.normalized.rules import RuleAction, RulebaseType
from frying_pan.normalized.scope import ScopeType
from frying_pan.normalized.services import Protocol, ServiceGroup, ServiceObject
from frying_pan.sources.base import SourceConfig, SourceType
from frying_pan.sources.panorama_xml import PanoramaXmlAdapter

FIXTURES = Path(__file__).parent / "fixtures"


def _parse_fixture(name: str) -> tuple:
    source_path = FIXTURES / "panorama" / name
    source = SourceConfig(
        display_name=name,
        original_path=source_path,
        source_type=SourceType.PANORAMA_XML,
    )

    return PanoramaXmlAdapter().parse(source), source_path


def test_panorama_parser_builds_scopes_from_reference_fixture() -> None:
    config, _ = _parse_fixture("reference_config_items.xml")
    scopes = {scope.path: scope for scope in config.scopes}

    assert scopes["shared"].scope_type == ScopeType.SHARED
    assert scopes["device-group/DEVICE-GROUP-1"].scope_type == ScopeType.DEVICE_GROUP
    assert scopes["device-group/CHILD-DG-1"].parent_path == "device-group/DEVICE-GROUP-1"
    assert scopes["device-group/DEVICE-GROUP-2"].scope_type == ScopeType.DEVICE_GROUP


def test_panorama_parser_extracts_shared_and_device_group_objects() -> None:
    config, _ = _parse_fixture("reference_config_items.xml")

    address = _entity(config.entities, AddressObject, "FP-REF-ADDR-FQDN-APP1")
    assert address.scope_path == "shared"
    assert address.address_kind == AddressKind.FQDN
    assert address.value == "app1.example.internal"

    address_group = _entity(config.entities, AddressGroup, "FP-REF-DG1-AG-APP")
    assert address_group.scope_path == "device-group/DEVICE-GROUP-1"
    assert address_group.members == ["FP-REF-DG1-ADDR-APP-A", "FP-REF-DG1-ADDR-OVERRIDE-ME"]

    dynamic_group = _entity(config.entities, AddressGroup, "FP-REF-AG-DYNAMIC-DMZ-TAG")
    assert dynamic_group.dynamic_filter == "'FP-REF-TAG-DMZ'"
    assert (
        "Dynamic address group shared/FP-REF-AG-DYNAMIC-DMZ-TAG filter is preserved "
        "but not evaluated."
    ) in config.warnings

    service = _entity(config.entities, ServiceObject, "FP-REF-SVC-UDP-1194")
    assert service.ports[0].protocol == Protocol.UDP
    assert service.ports[0].destination == "1194"

    service_group = _entity(config.entities, ServiceGroup, "FP-REF-SG-WEB-ALT")
    assert service_group.members == [
        "FP-REF-SVC-TCP-8443",
        "FP-REF-SVC-TCP-WEB-ALT",
        "service-http",
        "service-https",
    ]

    tag = _entity(config.entities, Tag, "FP-REF-TAG-DMZ")
    assert tag.color == "color2"
    assert tag.metadata["comments"] == "Reference tag for DMZ examples."


def test_panorama_parser_extracts_pre_and_post_security_rules() -> None:
    config, _ = _parse_fixture("reference_config_items.xml")

    pre_rule = next(
        rule for rule in config.security_rules if rule.name == "FP-REF-PRE-ALLOW-HQ-TO-DMZ-WEB"
    )
    assert pre_rule.scope_path == "device-group/DEVICE-GROUP-1"
    assert pre_rule.rulebase_type == RulebaseType.SECURITY_PRE
    assert pre_rule.position == 1
    assert pre_rule.source_zones == ["FP-REF-ZONE-TRUST"]
    assert pre_rule.destination_addresses == ["FP-REF-AG-STATIC-DMZ-SERVERS"]
    assert pre_rule.applications == ["web-browsing", "ssl"]
    assert pre_rule.services == ["application-default"]
    assert pre_rule.action == RuleAction.ALLOW

    post_rule = next(
        rule for rule in config.security_rules if rule.name == "FP-REF-POST-DENY-ANY-CLEANUP"
    )
    assert post_rule.rulebase_type == RulebaseType.SECURITY_POST
    assert post_rule.position == 2
    assert post_rule.action == RuleAction.DENY


def test_panorama_parser_handles_missing_optional_sections() -> None:
    config, _ = _parse_fixture("basic_panorama.xml")

    assert [scope.path for scope in config.scopes] == [
        "shared",
        "device-group/DG-A",
    ]
    assert config.entities == []
    assert config.security_rules == []


def test_panorama_parser_warns_on_unsupported_object_variants(tmp_path: Path) -> None:
    source_path = tmp_path / "unsupported_panorama.xml"
    source_path.write_text(
        """<config version="11.1.0">
  <shared>
    <address>
      <entry name="UNSUPPORTED-ADDR"><ip-wildcard>192.0.2.0/0.0.0.255</ip-wildcard></entry>
    </address>
    <service>
      <entry name="UNSUPPORTED-SVC"><protocol><icmp /></protocol></entry>
    </service>
  </shared>
  <devices><entry name="localhost.localdomain"><device-group /></entry></devices>
</config>""",
        encoding="utf-8",
    )
    source = SourceConfig(
        display_name=source_path.name,
        original_path=source_path,
        source_type=SourceType.PANORAMA_XML,
    )

    config = PanoramaXmlAdapter().parse(source)

    assert "Address object shared/UNSUPPORTED-ADDR has unsupported type." in config.warnings
    assert "Service object shared/UNSUPPORTED-SVC has unsupported protocol." in config.warnings


def _entity(entities: list, model_type: type, name: str):
    entity = next(entity for entity in entities if entity.name == name)
    assert entity.entity_type in {value for value in EntityType}
    assert isinstance(entity, model_type)
    return entity
