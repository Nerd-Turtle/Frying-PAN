from __future__ import annotations

from pathlib import Path

from frying_pan.normalized.config import NormalizedConfig
from frying_pan.normalized.references import Reference, ReferenceKind
from frying_pan.normalized.rules import RuleAction, RulebaseType, SecurityRule
from frying_pan.normalized.scope import ConfigScope, ScopeType
from frying_pan.policy.audit.audit_engine import PolicyAuditEngine
from frying_pan.policy.audit.findings import FindingType, PolicyAuditResult, Severity
from frying_pan.sources.base import SourceType
from frying_pan.sources.parsing import parse_source

FIXTURES = Path(__file__).parent / "fixtures"


def test_policy_audit_flags_broad_allow_scaffold() -> None:
    findings = PolicyAuditEngine().audit(
        "source-1",
        "shared/security",
        [SecurityRule(name="allow-any", scope_path="shared", action=RuleAction.ALLOW)],
    )

    assert findings
    assert findings[0].finding_type == FindingType.BROAD_ALLOW


def test_policy_audit_result_model_serializes_counts() -> None:
    result = PolicyAuditResult(
        source_id="source-1",
        source_type="firewall_xml",
        findings=[
            PolicyAuditEngine()
            .audit(
                "source-1",
                "vsys/vsys1",
                [
                    SecurityRule(
                        name="allow-any",
                        scope_path="vsys/vsys1",
                        action=RuleAction.ALLOW,
                    )
                ],
            )[0]
        ],
    )

    dumped = result.model_dump()

    assert dumped["finding_count"] == 1
    assert dumped["finding_counts_by_type"][FindingType.BROAD_ALLOW.value] == 1


def test_policy_audit_config_finds_firewall_fixture_findings() -> None:
    config = parse_source(FIXTURES / "firewall" / "reference_config_items_virtual_router.xml")

    result = PolicyAuditEngine().audit_config(config, "vsys/vsys1")
    finding_types = {finding.finding_type for finding in result.findings}

    assert result.audited_rule_count == 4
    assert FindingType.DISABLED_RULE in finding_types
    assert FindingType.CLEANUP_RULE in finding_types
    assert FindingType.APPLICATION_DEFAULT_REVIEW in finding_types
    assert any(
        finding.affected_rules == ["FP-REF-FW-DISABLED-ALLOW-EXAMPLE"]
        for finding in result.findings
        if finding.finding_type == FindingType.DISABLED_RULE
    )


def test_policy_audit_config_warns_for_panorama_local_rule_gap() -> None:
    config = parse_source(FIXTURES / "panorama" / "reference_config_items.xml")

    result = PolicyAuditEngine().audit_config(config, "device-group/DEVICE-GROUP-1")

    assert result.audited_rule_count == 4
    assert any("local firewall rules" in warning for warning in result.warnings)


def test_policy_audit_detects_duplicate_rule_and_full_shadow() -> None:
    rules = [
        SecurityRule(
            name="allow-any",
            scope_path="vsys/vsys1",
            rulebase_type=RulebaseType.SECURITY_LOCAL,
            position=1,
            action=RuleAction.ALLOW,
        ),
        SecurityRule(
            name="allow-web",
            scope_path="vsys/vsys1",
            rulebase_type=RulebaseType.SECURITY_LOCAL,
            position=2,
            source_zones=["trust"],
            destination_zones=["untrust"],
            services=["service-https"],
            action=RuleAction.ALLOW,
        ),
        SecurityRule(
            name="allow-web-copy",
            scope_path="vsys/vsys1",
            rulebase_type=RulebaseType.SECURITY_LOCAL,
            position=3,
            source_zones=["trust"],
            destination_zones=["untrust"],
            services=["service-https"],
            action=RuleAction.ALLOW,
        ),
    ]

    findings = PolicyAuditEngine().audit("source-1", "vsys/vsys1", rules)
    finding_types = {finding.finding_type for finding in findings}

    assert FindingType.DUPLICATE_RULE in finding_types
    assert FindingType.FULL_SHADOW in finding_types


def test_policy_audit_reports_unresolved_reference() -> None:
    config = NormalizedConfig(
        source_id="source-1",
        source_type=SourceType.FIREWALL_XML,
        scopes=[ConfigScope(name="vsys1", scope_type=ScopeType.VSYS, path="vsys/vsys1")],
        security_rules=[
            SecurityRule(
                name="allow-missing",
                scope_path="vsys/vsys1",
                rulebase_type=RulebaseType.SECURITY_LOCAL,
                position=1,
                source_addresses=["missing-address"],
                action=RuleAction.ALLOW,
            )
        ],
        references=[
            Reference(
                owner_scope_path="vsys/vsys1",
                owner_name="allow-missing",
                owner_type="security_rule",
                target_name="missing-address",
                reference_kind=ReferenceKind.RULE_SOURCE_ADDRESS,
                resolved=False,
                warnings=["Unresolved reference to 'missing-address'."],
            )
        ],
    )

    result = PolicyAuditEngine().audit_config(config, "vsys/vsys1")
    finding = next(
        finding
        for finding in result.findings
        if finding.finding_type == FindingType.MISSING_OBJECT_REFERENCE
    )

    assert finding.severity == Severity.MEDIUM
    assert finding.affected_match_criteria["target"] == "missing-address"
