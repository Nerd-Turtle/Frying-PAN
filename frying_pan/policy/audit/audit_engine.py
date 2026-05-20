from __future__ import annotations

from frying_pan.normalized.rules import RuleAction, SecurityRule
from frying_pan.policy.audit.findings import AuditFinding, FindingType, Severity


class PolicyAuditEngine:
    def audit(
        self, source_config: str, scope_or_rulebase: str, rules: list[SecurityRule]
    ) -> list[AuditFinding]:
        findings: list[AuditFinding] = []
        for rule in rules:
            if (
                rule.action == RuleAction.ALLOW
                and rule.source_zones == ["any"]
                and rule.destination_zones == ["any"]
                and rule.source_addresses == ["any"]
                and rule.destination_addresses == ["any"]
            ):
                findings.append(
                    AuditFinding(
                        finding_type=FindingType.BROAD_ALLOW,
                        severity=Severity.HIGH,
                        source_config=source_config,
                        scope_or_rulebase=scope_or_rulebase,
                        affected_rules=[rule.name],
                        explanation=(
                            "Rule broadly allows traffic across any source "
                            "and destination criteria."
                        ),
                        recommendation=(
                            "Review whether this rule should be narrowed "
                            "or explicitly justified."
                        ),
                        confidence="medium",
                    )
                )
        return findings
