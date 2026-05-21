from __future__ import annotations

from pathlib import Path

from frying_pan.normalized.addresses import AddressObject
from frying_pan.normalized.objects import Tag
from frying_pan.normalized.rules import RuleAction, RulebaseType
from frying_pan.normalized.scope import ScopeType
from frying_pan.normalized.services import ServiceGroup, ServiceObject
from frying_pan.sources.base import SourceConfig, SourceType
from frying_pan.sources.firewall_xml import FirewallXmlAdapter

FIXTURES = Path(__file__).parent / "fixtures"


def _parse_fixture(name: str):
    source_path = FIXTURES / "firewall" / name
    source = SourceConfig(
        display_name=name,
        original_path=source_path,
        source_type=SourceType.FIREWALL_XML,
    )

    return FirewallXmlAdapter().parse(source)


def test_firewall_parser_builds_vsys_scope_without_panorama_assumptions() -> None:
    config = _parse_fixture("reference_firewall.xml")

    assert len(config.scopes) == 1
    assert config.scopes[0].name == "vsys1"
    assert config.scopes[0].path == "vsys/vsys1"
    assert config.scopes[0].scope_type == ScopeType.VSYS
    assert config.scopes[0].parent_path is None


def test_firewall_parser_extracts_vsys_objects() -> None:
    config = _parse_fixture("reference_firewall.xml")

    address = _entity(config.entities, AddressObject, "FW-REF-ADDR-USERS")
    assert address.scope_path == "vsys/vsys1"
    assert address.value == "10.60.10.0/24"

    service = _entity(config.entities, ServiceObject, "FW-REF-SVC-TCP-8443")
    assert service.ports[0].destination == "8443"

    service_group = _entity(config.entities, ServiceGroup, "FW-REF-SG-WEB")
    assert service_group.members == ["FW-REF-SVC-TCP-8443", "service-https"]

    tag = _entity(config.entities, Tag, "FW-REF-TAG-LOCAL")
    assert tag.color == "color7"


def test_firewall_parser_extracts_local_security_rules() -> None:
    config = _parse_fixture("reference_firewall.xml")

    rule = config.security_rules[0]
    assert rule.name == "FW-REF-ALLOW-USERS-WEB"
    assert rule.scope_path == "vsys/vsys1"
    assert rule.rulebase_type == RulebaseType.SECURITY_LOCAL
    assert rule.position == 1
    assert rule.source_zones == ["trust"]
    assert rule.destination_addresses == ["FW-REF-AG-WEB"]
    assert rule.services == ["FW-REF-SVC-TCP-8443"]
    assert rule.action == RuleAction.ALLOW


def test_firewall_parser_preserves_disabled_rule_and_url_category() -> None:
    config = _parse_fixture("reference_config_items_virtual_router.xml")

    allow_rule = next(
        rule for rule in config.security_rules if rule.name == "FP-REF-FW-ALLOW-USERS-TO-DMZ-WEB"
    )
    disabled_rule = next(
        rule for rule in config.security_rules if rule.name == "FP-REF-FW-DISABLED-ALLOW-EXAMPLE"
    )

    assert allow_rule.url_categories == ["FP-REF-FW-URLCAT-EXAMPLE"]
    assert disabled_rule.metadata["disabled"] is True


def test_firewall_parser_handles_missing_optional_sections() -> None:
    config = _parse_fixture("basic_firewall.xml")

    assert [scope.path for scope in config.scopes] == ["vsys/vsys1"]
    assert config.entities == []
    assert config.security_rules == []


def test_firewall_parser_loads_full_virtual_router_and_advanced_routing_fixtures() -> None:
    for fixture_name in (
        "reference_config_items_virtual_router.xml",
        "reference_config_items_advanced_routing.xml",
    ):
        config = _parse_fixture(fixture_name)

        assert [scope.path for scope in config.scopes] == ["vsys/vsys1"]
        assert len(config.entities) == 14
        assert [rule.name for rule in config.security_rules] == [
            "FP-REF-FW-ALLOW-USERS-TO-DMZ-WEB",
            "FP-REF-FW-DENY-GUEST-TO-DMZ",
            "FP-REF-FW-DISABLED-ALLOW-EXAMPLE",
            "FP-REF-FW-DROP-CLEANUP",
        ]


def _entity(entities: list, model_type: type, name: str):
    entity = next(entity for entity in entities if entity.name == name)
    assert isinstance(entity, model_type)
    return entity
