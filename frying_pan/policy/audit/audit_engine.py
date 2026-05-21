from __future__ import annotations

from collections.abc import Iterable

from frying_pan.normalized.config import NormalizedConfig
from frying_pan.normalized.references import Reference, ReferenceKind
from frying_pan.normalized.rules import RuleAction, SecurityRule
from frying_pan.policy.audit.findings import (
    AuditFinding,
    FindingType,
    PolicyAuditResult,
    Severity,
)
from frying_pan.policy.match.match_engine import PolicyMatchEngine

_IGNORED_REFERENCE_TARGETS = {"any", "", "service-http", "service-https", "application-default"}


class PolicyAuditEngine:
    def audit(
        self, source_config: str, scope_or_rulebase: str, rules: list[SecurityRule]
    ) -> list[AuditFinding]:
        ordered_rules = sorted(rules, key=lambda rule: rule.position)
        return self._audit_ordered_rules(source_config, scope_or_rulebase, ordered_rules, [])

    def audit_config(
        self, config: NormalizedConfig, scope_path: str | None = None
    ) -> PolicyAuditResult:
        match_engine = PolicyMatchEngine()
        if scope_path is None:
            selected_scope = None
            rules = self._whole_config_rules(config)
            warnings = [
                "Whole-config audit reviews parsed rule records directly; use --scope for "
                "effective Panorama Device Group ordering with inherited rules."
            ]
            findings = self._audit_ordered_rules(
                config.source_id, "all audited scopes", rules, config.references
            )
        else:
            rules, warnings, selected_scope = match_engine.ordered_rules_for_scope(
                config, scope_path
            )
            findings = self._audit_ordered_rules(
                config.source_id, selected_scope or "all", rules, config.references
            )
        result = PolicyAuditResult(
            source_id=config.source_id,
            source_type=config.source_type.value,
            scope_path=selected_scope,
            audited_rule_count=len(rules),
            findings=findings,
            warnings=_dedupe(warnings),
        )
        return result

    def _whole_config_rules(self, config: NormalizedConfig) -> list[SecurityRule]:
        rulebase_order = {
            "security_pre": 0,
            "security_local": 1,
            "security_post": 2,
        }
        return sorted(
            config.security_rules,
            key=lambda rule: (
                rule.scope_path,
                rulebase_order.get(rule.rulebase_type.value, 99),
                rule.position,
            ),
        )

    def _audit_ordered_rules(
        self,
        source_config: str,
        scope_or_rulebase: str,
        rules: list[SecurityRule],
        references: list[Reference],
    ) -> list[AuditFinding]:
        findings: list[AuditFinding] = []
        findings.extend(
            self._missing_reference_findings(source_config, scope_or_rulebase, references)
        )
        findings.extend(self._duplicate_rule_findings(source_config, scope_or_rulebase, rules))
        findings.extend(self._full_shadow_findings(source_config, scope_or_rulebase, rules))
        findings.extend(self._broad_allow_findings(source_config, scope_or_rulebase, rules))
        findings.extend(self._cleanup_findings(source_config, scope_or_rulebase, rules))
        findings.extend(self._disabled_rule_findings(source_config, scope_or_rulebase, rules))
        findings.extend(self._logging_findings(source_config, scope_or_rulebase, rules))
        findings.extend(self._appid_service_findings(source_config, scope_or_rulebase, rules))
        return [
            finding.model_copy(update={"finding_id": f"PA-{index:04d}"})
            for index, finding in enumerate(findings, start=1)
        ]

    def _missing_reference_findings(
        self, source_config: str, scope_or_rulebase: str, references: list[Reference]
    ) -> list[AuditFinding]:
        findings: list[AuditFinding] = []
        for reference in references:
            if reference.resolved or reference.target_name in _IGNORED_REFERENCE_TARGETS:
                continue
            if reference.reference_kind == ReferenceKind.TAG:
                severity = Severity.LOW
            elif "zone" in reference.reference_kind.value:
                severity = Severity.LOW
            else:
                severity = Severity.MEDIUM
            findings.append(
                AuditFinding(
                    finding_type=FindingType.MISSING_OBJECT_REFERENCE,
                    severity=severity,
                    source_config=source_config,
                    scope_or_rulebase=scope_or_rulebase,
                    affected_rules=[reference.owner_name],
                    affected_match_criteria={
                        "reference_kind": reference.reference_kind.value,
                        "target": reference.target_name,
                    },
                    explanation=(
                        f"{reference.owner_name} references {reference.target_name!r}, "
                        "but the target was not resolved in parsed inventory."
                    ),
                    recommendation=(
                        "Review whether this is a built-in, runtime-only object, or a missing "
                        "configuration dependency."
                    ),
                    confidence="high",
                    warnings=reference.warnings,
                    metadata={"owner_type": reference.owner_type},
                )
            )
        return findings

    def _duplicate_rule_findings(
        self, source_config: str, scope_or_rulebase: str, rules: list[SecurityRule]
    ) -> list[AuditFinding]:
        findings: list[AuditFinding] = []
        seen: dict[tuple, SecurityRule] = {}
        for rule in rules:
            key = _rule_fingerprint(rule, include_action=True)
            previous = seen.get(key)
            if previous is not None:
                findings.append(
                    AuditFinding(
                        finding_type=FindingType.DUPLICATE_RULE,
                        severity=Severity.MEDIUM,
                        source_config=source_config,
                        scope_or_rulebase=scope_or_rulebase,
                        affected_rules=[previous.name, rule.name],
                        affected_match_criteria=_criteria_summary(rule),
                        explanation=(
                            f"{rule.name} has the same supported match criteria and action "
                            f"as earlier rule {previous.name}."
                        ),
                        recommendation=(
                            "Review whether one duplicate rule can be removed or justified."
                        ),
                        confidence="high",
                    )
                )
            else:
                seen[key] = rule
        return findings

    def _full_shadow_findings(
        self, source_config: str, scope_or_rulebase: str, rules: list[SecurityRule]
    ) -> list[AuditFinding]:
        findings: list[AuditFinding] = []
        # PAN-OS first-match means an earlier broad match can make a later rule unreachable.
        # Ref: https://docs.paloaltonetworks.com/pan-os/11-1/pan-os-admin/policy/security-policy
        for index, rule in enumerate(rules):
            if rule.metadata.get("disabled") is True:
                continue
            for earlier in rules[:index]:
                if earlier.metadata.get("disabled") is True:
                    continue
                if _rule_covers(earlier, rule):
                    severity = (
                        Severity.HIGH if earlier.action != rule.action else Severity.MEDIUM
                    )
                    findings.append(
                        AuditFinding(
                            finding_type=FindingType.FULL_SHADOW,
                            severity=severity,
                            source_config=source_config,
                            scope_or_rulebase=scope_or_rulebase,
                            affected_rules=[earlier.name, rule.name],
                            affected_match_criteria=_criteria_summary(rule),
                            explanation=(
                                f"{rule.name} is obviously covered by earlier rule "
                                f"{earlier.name} for supported match criteria."
                            ),
                            recommendation=(
                                "Review ordering and confirm whether the later rule is reachable."
                            ),
                            confidence="medium",
                        )
                    )
                    break
        return findings

    def _broad_allow_findings(
        self, source_config: str, scope_or_rulebase: str, rules: list[SecurityRule]
    ) -> list[AuditFinding]:
        findings: list[AuditFinding] = []
        for rule in rules:
            if rule.action == RuleAction.ALLOW and _is_catch_all(rule):
                findings.append(
                    AuditFinding(
                        finding_type=FindingType.BROAD_ALLOW,
                        severity=Severity.HIGH,
                        source_config=source_config,
                        scope_or_rulebase=scope_or_rulebase,
                        affected_rules=[rule.name],
                        affected_match_criteria=_criteria_summary(rule),
                        explanation=(
                            "Rule broadly allows traffic across any supported source, "
                            "destination, application, service, user, and URL category criteria."
                        ),
                        recommendation=(
                            "Review whether this rule should be narrowed, moved, or explicitly "
                            "justified."
                        ),
                        confidence="high",
                    )
                )
        return findings

    def _cleanup_findings(
        self, source_config: str, scope_or_rulebase: str, rules: list[SecurityRule]
    ) -> list[AuditFinding]:
        enabled_rules = [rule for rule in rules if rule.metadata.get("disabled") is not True]
        if not enabled_rules:
            return []
        last_rule = enabled_rules[-1]
        if _is_catch_all(last_rule):
            severity = Severity.MEDIUM if last_rule.action == RuleAction.ALLOW else Severity.INFO
            return [
                AuditFinding(
                    finding_type=FindingType.CLEANUP_RULE,
                    severity=severity,
                    source_config=source_config,
                    scope_or_rulebase=scope_or_rulebase,
                    affected_rules=[last_rule.name],
                    affected_match_criteria=_criteria_summary(last_rule),
                    explanation=(
                        f"Last enabled rule is an explicit catch-all {last_rule.action} rule."
                    ),
                    recommendation="Review cleanup posture and logging.",
                    confidence="high",
                )
            ]
        return [
            AuditFinding(
                finding_type=FindingType.MISSING_CLEANUP,
                severity=Severity.LOW,
                source_config=source_config,
                scope_or_rulebase=scope_or_rulebase,
                affected_rules=[],
                explanation=(
                    "No explicit catch-all cleanup rule was found at the end of the audited "
                    "rule sequence."
                ),
                recommendation=(
                    "Review whether relying on predefined default rules is intentional."
                ),
                confidence="medium",
                warnings=[
                    "Phase 3 does not synthesize PAN-OS predefined "
                    "intrazone/interzone default rules."
                ],
            )
        ]

    def _disabled_rule_findings(
        self, source_config: str, scope_or_rulebase: str, rules: list[SecurityRule]
    ) -> list[AuditFinding]:
        return [
            AuditFinding(
                finding_type=FindingType.DISABLED_RULE,
                severity=Severity.INFO,
                source_config=source_config,
                scope_or_rulebase=scope_or_rulebase,
                affected_rules=[rule.name],
                explanation=f"{rule.name} is disabled in the imported configuration.",
                recommendation="Confirm whether the disabled rule should be retained.",
                confidence="high",
            )
            for rule in rules
            if rule.metadata.get("disabled") is True
        ]

    def _logging_findings(
        self, source_config: str, scope_or_rulebase: str, rules: list[SecurityRule]
    ) -> list[AuditFinding]:
        findings: list[AuditFinding] = []
        for rule in rules:
            if rule.metadata.get("disabled") is True:
                continue
            if rule.metadata.get("log_end") != "yes":
                findings.append(
                    AuditFinding(
                        finding_type=FindingType.LOGGING_GAP,
                        severity=Severity.LOW,
                        source_config=source_config,
                        scope_or_rulebase=scope_or_rulebase,
                        affected_rules=[rule.name],
                        explanation=(
                            f"{rule.name} does not have parsed log-at-session-end enabled."
                        ),
                        recommendation="Review rule logging posture.",
                        confidence="medium",
                    )
                )
        return findings

    def _appid_service_findings(
        self, source_config: str, scope_or_rulebase: str, rules: list[SecurityRule]
    ) -> list[AuditFinding]:
        findings: list[AuditFinding] = []
        for rule in rules:
            if rule.metadata.get("disabled") is True or rule.action != RuleAction.ALLOW:
                continue
            if "application-default" in rule.services:
                # application-default is App-ID/content dependent, so audit labels it for review.
                # Ref: https://docs.paloaltonetworks.com/pan-os/11-0/pan-os-admin/app-id/application-default
                findings.append(
                    AuditFinding(
                        finding_type=FindingType.APPLICATION_DEFAULT_REVIEW,
                        severity=Severity.LOW,
                        source_config=source_config,
                        scope_or_rulebase=scope_or_rulebase,
                        affected_rules=[rule.name],
                        affected_match_criteria={"service": "application-default"},
                        explanation=(
                            f"{rule.name} uses application-default; exact default-port "
                            "behavior depends on App-ID content and runtime classification."
                        ),
                        recommendation=(
                            "Review application-default behavior for the allowed applications."
                        ),
                        confidence="medium",
                    )
                )
            elif not _is_any(rule.applications) and _is_any(rule.services):
                findings.append(
                    AuditFinding(
                        finding_type=FindingType.APP_ID_GAP,
                        severity=Severity.LOW,
                        source_config=source_config,
                        scope_or_rulebase=scope_or_rulebase,
                        affected_rules=[rule.name],
                        affected_match_criteria={"application": ",".join(rule.applications)},
                        explanation=(
                            f"{rule.name} allows explicit applications with service any."
                        ),
                        recommendation=(
                            "Review whether application-default or explicit services are preferred."
                        ),
                        confidence="medium",
                    )
                )
            elif _is_any(rule.applications) and not _is_any(rule.services):
                findings.append(
                    AuditFinding(
                        finding_type=FindingType.PORT_BASED_ALLOW,
                        severity=Severity.MEDIUM,
                        source_config=source_config,
                        scope_or_rulebase=scope_or_rulebase,
                        affected_rules=[rule.name],
                        affected_match_criteria={"service": ",".join(rule.services)},
                        explanation=(
                            f"{rule.name} allows traffic by service while application is any."
                        ),
                        recommendation=(
                            "Review whether App-ID criteria should narrow this allow rule."
                        ),
                        confidence="medium",
                    )
                )
        return findings


def _rule_fingerprint(rule: SecurityRule, *, include_action: bool) -> tuple:
    values: list[object] = [
        tuple(sorted(rule.source_zones)),
        tuple(sorted(rule.destination_zones)),
        tuple(sorted(rule.source_addresses)),
        tuple(sorted(rule.destination_addresses)),
        tuple(sorted(rule.applications)),
        tuple(sorted(rule.services)),
        tuple(sorted(rule.users)),
        tuple(sorted(rule.url_categories or ["any"])),
    ]
    if include_action:
        values.append(rule.action)
    return tuple(values)


def _rule_covers(earlier: SecurityRule, later: SecurityRule) -> bool:
    checks = (
        _selector_covers(earlier.source_zones, later.source_zones),
        _selector_covers(earlier.destination_zones, later.destination_zones),
        _selector_covers(earlier.source_addresses, later.source_addresses),
        _selector_covers(earlier.destination_addresses, later.destination_addresses),
        _selector_covers(earlier.applications, later.applications),
        _selector_covers(earlier.services, later.services),
        _selector_covers(earlier.users, later.users),
        _selector_covers(earlier.url_categories or ["any"], later.url_categories or ["any"]),
    )
    return all(checks)


def _selector_covers(earlier: list[str], later: list[str]) -> bool:
    if _is_any(earlier):
        return True
    if _is_any(later):
        return False
    return set(later).issubset(set(earlier))


def _criteria_summary(rule: SecurityRule) -> dict[str, str]:
    return {
        "source_zones": ",".join(rule.source_zones),
        "destination_zones": ",".join(rule.destination_zones),
        "source_addresses": ",".join(rule.source_addresses),
        "destination_addresses": ",".join(rule.destination_addresses),
        "applications": ",".join(rule.applications),
        "services": ",".join(rule.services),
        "users": ",".join(rule.users),
        "url_categories": ",".join(rule.url_categories or ["any"]),
        "action": rule.action.value,
    }


def _is_catch_all(rule: SecurityRule) -> bool:
    return all(
        (
            _is_any(rule.source_zones),
            _is_any(rule.destination_zones),
            _is_any(rule.source_addresses),
            _is_any(rule.destination_addresses),
            _is_any(rule.applications),
            _is_any(rule.services),
            _is_any(rule.users),
            not rule.url_categories or _is_any(rule.url_categories),
        )
    )


def _is_any(values: Iterable[str]) -> bool:
    return "any" in values


def _dedupe(values: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(values))
