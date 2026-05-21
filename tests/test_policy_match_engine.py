from __future__ import annotations

from pathlib import Path

import pytest

from frying_pan.normalized.addresses import AddressKind, AddressObject
from frying_pan.normalized.config import NormalizedConfig
from frying_pan.normalized.rules import RuleAction, RulebaseType, SecurityRule
from frying_pan.normalized.scope import ConfigScope, ScopeType
from frying_pan.normalized.services import Protocol, ServiceGroup, ServiceObject, ServicePort
from frying_pan.policy.match.match_engine import PolicyMatchEngine
from frying_pan.policy.match.test_case import PolicyTestCase
from frying_pan.sources.base import SourceType
from frying_pan.sources.parsing import parse_source

FIXTURES = Path(__file__).parent / "fixtures"


def test_policy_match_engine_uses_first_match() -> None:
    rules = [
        SecurityRule(name="allow-first", scope_path="shared", position=1, action=RuleAction.ALLOW),
        SecurityRule(name="deny-later", scope_path="shared", position=2, action=RuleAction.DENY),
    ]
    test_case = PolicyTestCase(
        source_zone="trust",
        destination_zone="untrust",
        source_ip="192.0.2.10",
        destination_ip="198.51.100.20",
        protocol="tcp",
        destination_port=443,
    )

    result = PolicyMatchEngine().evaluate(rules, test_case)

    assert result.matched_rule is not None
    assert result.matched_rule.name == "allow-first"
    assert result.action == RuleAction.ALLOW
    assert [rule.name for rule in result.later_matching_rules] == ["deny-later"]


def test_policy_test_case_normalizes_and_rejects_invalid_inputs() -> None:
    test_case = PolicyTestCase(
        source_zone=" trust ",
        destination_zone="untrust",
        source_ip="192.0.2.8",
        destination_ip="198.51.100.20",
        protocol="TCP",
        destination_port=443,
    )

    assert test_case.source_zone == "trust"
    assert test_case.source_ip == "192.0.2.8"
    assert test_case.protocol == "tcp"

    with pytest.raises(ValueError):
        PolicyTestCase(
            source_zone="trust",
            destination_zone="untrust",
            source_ip="192.0.2.1",
            destination_ip="198.51.100.20",
            protocol="icmp",
        )

    with pytest.raises(ValueError):
        PolicyTestCase(
            source_zone="trust",
            destination_zone="untrust",
            source_ip="192.0.2.1",
            destination_ip="198.51.100.20",
            protocol="tcp",
            destination_port=70000,
        )


def test_policy_match_engine_resolves_firewall_address_and_application_default() -> None:
    config = parse_source(FIXTURES / "firewall" / "reference_config_items_virtual_router.xml")
    test_case = PolicyTestCase(
        source_zone="FP-REF-FW-ZONE-TRUST",
        destination_zone="FP-REF-FW-ZONE-DMZ",
        source_ip="10.60.10.10",
        destination_ip="10.70.10.10",
        protocol="tcp",
        destination_port=443,
        application="web-browsing",
        url_category="FP-REF-FW-URLCAT-EXAMPLE",
    )

    result = PolicyMatchEngine().evaluate_config(config, test_case, "vsys/vsys1")

    assert result.matched_rule is not None
    assert result.matched_rule.name == "FP-REF-FW-ALLOW-USERS-TO-DMZ-WEB"
    assert result.action == RuleAction.ALLOW
    assert any("application-default" in warning for warning in result.warnings)


def test_policy_match_engine_skips_disabled_rule_and_records_cleanup() -> None:
    config = parse_source(FIXTURES / "firewall" / "reference_config_items_virtual_router.xml")
    test_case = PolicyTestCase(
        source_zone="FP-REF-FW-ZONE-TRUST",
        destination_zone="FP-REF-FW-ZONE-DMZ",
        source_ip="10.99.1.10",
        destination_ip="10.70.10.20",
        protocol="tcp",
        destination_port=8443,
        application="ssl",
    )

    result = PolicyMatchEngine().evaluate_config(config, test_case, "vsys/vsys1")

    disabled_trace = next(
        step for step in result.trace if step.rule_name == "FP-REF-FW-DISABLED-ALLOW-EXAMPLE"
    )
    assert disabled_trace.matched is False
    assert disabled_trace.reason == "rule is disabled"
    assert result.matched_rule is not None
    assert result.matched_rule.name == "FP-REF-FW-DROP-CLEANUP"


def test_policy_match_engine_selects_panorama_pre_before_post_and_warns_local_gap() -> None:
    config = parse_source(FIXTURES / "panorama" / "reference_config_items.xml")
    test_case = PolicyTestCase(
        source_zone="FP-REF-ZONE-TRUST",
        destination_zone="FP-REF-ZONE-DMZ",
        source_ip="10.10.10.5",
        destination_ip="10.20.10.10",
        protocol="tcp",
        destination_port=443,
        application="web-browsing",
    )

    result = PolicyMatchEngine().evaluate_config(config, test_case, "device-group/CHILD-DG-1")

    assert result.matched_rule is not None
    assert result.matched_rule.name == "FP-REF-PRE-ALLOW-HQ-TO-DMZ-WEB"
    assert [step.rule_name for step in result.trace][:3] == [
        "FP-REF-PRE-ALLOW-HQ-TO-DMZ-WEB",
        "FP-REF-PRE-DENY-GUEST-TO-APP",
        "FP-REF-CHILD-PRE-ALLOW-OVERRIDE-APP",
    ]
    assert any("local firewall rules" in warning for warning in result.warnings)


def test_policy_match_engine_resolves_service_groups_and_later_matches() -> None:
    config = NormalizedConfig(
        source_id="synthetic",
        source_type=SourceType.FIREWALL_XML,
        scopes=[ConfigScope(name="vsys1", scope_type=ScopeType.VSYS, path="vsys/vsys1")],
        entities=[
            AddressObject(
                name="src-net",
                scope_path="vsys/vsys1",
                address_kind=AddressKind.IP_NETMASK,
                value="10.0.0.0/24",
            ),
            AddressObject(
                name="dst-host",
                scope_path="vsys/vsys1",
                address_kind=AddressKind.IP_NETMASK,
                value="192.0.2.10",
            ),
            ServiceObject(
                name="tcp-8443",
                scope_path="vsys/vsys1",
                ports=[ServicePort(protocol=Protocol.TCP, destination="8443")],
            ),
            ServiceGroup(name="web-sg", scope_path="vsys/vsys1", members=["tcp-8443"]),
        ],
        security_rules=[
            SecurityRule(
                name="allow-specific",
                scope_path="vsys/vsys1",
                rulebase_type=RulebaseType.SECURITY_LOCAL,
                position=1,
                source_addresses=["src-net"],
                destination_addresses=["dst-host"],
                services=["web-sg"],
                action=RuleAction.ALLOW,
            ),
            SecurityRule(
                name="deny-later",
                scope_path="vsys/vsys1",
                rulebase_type=RulebaseType.SECURITY_LOCAL,
                position=2,
                action=RuleAction.DENY,
            ),
        ],
    )
    test_case = PolicyTestCase(
        source_zone="trust",
        destination_zone="untrust",
        source_ip="10.0.0.5",
        destination_ip="192.0.2.10",
        protocol="tcp",
        destination_port=8443,
    )

    result = PolicyMatchEngine().evaluate_config(config, test_case, "vsys/vsys1")

    assert result.matched_rule is not None
    assert result.matched_rule.name == "allow-specific"
    assert [rule.name for rule in result.later_matching_rules] == ["deny-later"]


def test_policy_match_engine_warns_on_unsupported_service_port_syntax() -> None:
    config = NormalizedConfig(
        source_id="synthetic",
        source_type=SourceType.FIREWALL_XML,
        scopes=[ConfigScope(name="vsys1", scope_type=ScopeType.VSYS, path="vsys/vsys1")],
        entities=[
            ServiceObject(
                name="bad-service",
                scope_path="vsys/vsys1",
                ports=[ServicePort(protocol=Protocol.TCP, destination="not-a-port")],
            )
        ],
        security_rules=[
            SecurityRule(
                name="bad-service-rule",
                scope_path="vsys/vsys1",
                rulebase_type=RulebaseType.SECURITY_LOCAL,
                position=1,
                services=["bad-service"],
                action=RuleAction.ALLOW,
            )
        ],
    )
    test_case = PolicyTestCase(
        source_zone="trust",
        destination_zone="untrust",
        source_ip="10.0.0.5",
        destination_ip="192.0.2.10",
        protocol="tcp",
        destination_port=8443,
    )

    result = PolicyMatchEngine().evaluate_config(config, test_case, "vsys/vsys1")

    assert result.matched_rule is None
    assert any("unsupported port syntax" in warning for warning in result.warnings)
