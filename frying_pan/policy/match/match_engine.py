from __future__ import annotations

from frying_pan.normalized.rules import SecurityRule
from frying_pan.policy.match.match_trace import MatchTraceStep
from frying_pan.policy.match.result import PolicyMatchResult
from frying_pan.policy.match.test_case import PolicyTestCase


class PolicyMatchEngine:
    def evaluate(self, rules: list[SecurityRule], test_case: PolicyTestCase) -> PolicyMatchResult:
        ordered_rules = sorted(rules, key=lambda rule: rule.position)
        result = PolicyMatchResult()
        first_match_found = False

        # PAN-OS security policy evaluates top-down and stops at the first matching rule.
        # Ref: https://docs.paloaltonetworks.com/pan-os/11-1/pan-os-admin/policy/security-policy
        for rule in ordered_rules:
            matched, reason, warnings = self._rule_matches(rule, test_case)
            result.trace.append(
                MatchTraceStep(
                    rule_name=rule.name, matched=matched, reason=reason, warnings=warnings
                )
            )
            result.warnings.extend(warnings)
            if matched and not first_match_found:
                result.matched_rule = rule
                result.action = rule.action
                first_match_found = True
            elif matched:
                result.later_matching_rules.append(rule)

        return result

    def _rule_matches(
        self, rule: SecurityRule, test_case: PolicyTestCase
    ) -> tuple[bool, str, list[str]]:
        warnings: list[str] = []
        checks = [
            ("source zone", test_case.source_zone, rule.source_zones),
            ("destination zone", test_case.destination_zone, rule.destination_zones),
            ("application", test_case.application, rule.applications),
            ("user", test_case.user, rule.users),
        ]
        for label, value, allowed_values in checks:
            if "any" not in allowed_values and value not in allowed_values:
                return False, f"{label} {value!r} is not in rule criteria", warnings

        if "application-default" in rule.services:
            warnings.append(
                "Rule uses application-default; offline matching cannot fully simulate App-ID."
            )

        return True, "basic criteria matched; address and service resolution are pending", warnings
