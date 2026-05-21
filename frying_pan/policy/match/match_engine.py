from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from ipaddress import ip_address, ip_network

from frying_pan.normalized.addresses import AddressGroup, AddressKind, AddressObject
from frying_pan.normalized.config import NormalizedConfig
from frying_pan.normalized.entity import NormalizedEntity
from frying_pan.normalized.rules import RulebaseType, SecurityRule
from frying_pan.normalized.scope import ScopeType
from frying_pan.normalized.services import Protocol, ServiceGroup, ServiceObject, ServicePort
from frying_pan.policy.match.match_trace import MatchTraceStep
from frying_pan.policy.match.result import PolicyMatchResult
from frying_pan.policy.match.test_case import PolicyTestCase

_BUILTIN_SERVICES = {
    "service-http": ("tcp", "80"),
    "service-https": ("tcp", "443"),
}


@dataclass
class _CriterionResult:
    label: str
    matched: bool
    detail: str
    warnings: list[str] = field(default_factory=list)


class PolicyMatchEngine:
    def evaluate(self, rules: list[SecurityRule], test_case: PolicyTestCase) -> PolicyMatchResult:
        ordered_rules = sorted(rules, key=lambda rule: rule.position)
        return self._evaluate_ordered_rules(ordered_rules, test_case, scope_path=None, config=None)

    def evaluate_config(
        self,
        config: NormalizedConfig,
        test_case: PolicyTestCase,
        scope_path: str | None = None,
    ) -> PolicyMatchResult:
        selected_scope = scope_path or self._default_scope_path(config)
        rules, warnings = self._rules_for_scope(config, selected_scope)
        result = self._evaluate_ordered_rules(
            rules, test_case, scope_path=selected_scope, config=config
        )
        result.warnings = [*warnings, *result.warnings]
        return result

    def _evaluate_ordered_rules(
        self,
        ordered_rules: list[SecurityRule],
        test_case: PolicyTestCase,
        *,
        scope_path: str | None,
        config: NormalizedConfig | None,
    ) -> PolicyMatchResult:
        result = PolicyMatchResult(scope_path=scope_path, evaluated_rule_count=len(ordered_rules))
        first_match_found = False

        # PAN-OS security policy evaluates top-down and stops at the first matching rule.
        # Ref: https://docs.paloaltonetworks.com/pan-os/11-1/pan-os-admin/policy/security-policy
        for rule in ordered_rules:
            rule_result = self._rule_matches(rule, test_case, config)
            result.trace.append(
                MatchTraceStep(
                    rule_name=rule.name,
                    matched=rule_result.matched,
                    reason=rule_result.detail,
                    warnings=rule_result.warnings,
                    criteria={rule_result.label: rule_result.matched}
                    if rule_result.label == "disabled"
                    else self._criteria_map(rule, test_case, config),
                    details=self._criteria_details(rule, test_case, config),
                    position=rule.position,
                    rulebase_type=rule.rulebase_type.value,
                    action=rule.action,
                )
            )
            result.warnings.extend(rule_result.warnings)
            if rule_result.matched and not first_match_found:
                result.matched_rule = rule
                result.action = rule.action
                first_match_found = True
            elif rule_result.matched:
                result.later_matching_rules.append(rule)

        result.warnings = _dedupe(result.warnings)
        return result

    def _rule_matches(
        self,
        rule: SecurityRule,
        test_case: PolicyTestCase,
        config: NormalizedConfig | None,
    ) -> _CriterionResult:
        if rule.metadata.get("disabled") is True:
            return _CriterionResult("disabled", False, "rule is disabled")

        checks = self._criteria(rule, test_case, config)
        warnings = _dedupe(warning for check in checks for warning in check.warnings)
        failed = next((check for check in checks if not check.matched), None)
        if failed is not None:
            return _CriterionResult(
                failed.label,
                False,
                f"{failed.label} did not match: {failed.detail}",
                warnings,
            )
        return _CriterionResult(
            "all",
            True,
            "all supported criteria matched or were conservatively treated as possible matches",
            warnings,
        )

    def _criteria(
        self,
        rule: SecurityRule,
        test_case: PolicyTestCase,
        config: NormalizedConfig | None,
    ) -> list[_CriterionResult]:
        return [
            self._selector_match("source zone", test_case.source_zone, rule.source_zones),
            self._selector_match(
                "destination zone", test_case.destination_zone, rule.destination_zones
            ),
            self._address_match(
                "source address",
                test_case.source_ip,
                rule.source_addresses,
                rule.scope_path,
                config,
            ),
            self._address_match(
                "destination address",
                test_case.destination_ip,
                rule.destination_addresses,
                rule.scope_path,
                config,
            ),
            self._application_match(test_case.application, rule.applications),
            self._service_match(test_case, rule.services, rule.scope_path, config),
            self._user_match(test_case.user, rule.users),
            self._url_category_match(test_case.url_category, rule.url_categories),
            self._hip_match(test_case, rule),
        ]

    def _criteria_map(
        self,
        rule: SecurityRule,
        test_case: PolicyTestCase,
        config: NormalizedConfig | None,
    ) -> dict[str, bool]:
        return {check.label: check.matched for check in self._criteria(rule, test_case, config)}

    def _criteria_details(
        self,
        rule: SecurityRule,
        test_case: PolicyTestCase,
        config: NormalizedConfig | None,
    ) -> list[str]:
        return [
            f"{check.label}: {check.detail}"
            for check in self._criteria(rule, test_case, config)
        ]

    def _selector_match(
        self, label: str, value: str | None, allowed_values: list[str]
    ) -> _CriterionResult:
        if _is_any(allowed_values):
            return _CriterionResult(label, True, "rule uses any")
        if value in allowed_values:
            return _CriterionResult(label, True, f"{value!r} matched explicitly")
        return _CriterionResult(label, False, f"{value!r} is not in {allowed_values!r}")

    def _address_match(
        self,
        label: str,
        ip_value: str,
        selectors: list[str],
        scope_path: str,
        config: NormalizedConfig | None,
    ) -> _CriterionResult:
        if _is_any(selectors):
            return _CriterionResult(label, True, "rule uses any")

        warnings: list[str] = []
        matched = False
        details: list[str] = []
        for selector in selectors:
            selector_match, selector_detail, selector_warnings = self._address_selector_matches(
                selector, ip_value, scope_path, config, seen=set()
            )
            warnings.extend(selector_warnings)
            details.append(f"{selector}: {selector_detail}")
            matched = matched or selector_match

        return _CriterionResult(label, matched, "; ".join(details), _dedupe(warnings))

    def _address_selector_matches(
        self,
        selector: str,
        ip_value: str,
        scope_path: str,
        config: NormalizedConfig | None,
        *,
        seen: set[str],
    ) -> tuple[bool, str, list[str]]:
        if selector == "any":
            return True, "any", []

        try:
            network = ip_network(selector, strict=False)
        except ValueError:
            network = None
        if network is not None:
            return ip_address(ip_value) in network, f"literal network {network}", []

        if config is None:
            return False, "object resolution unavailable without normalized config", [
                f"Address selector {selector!r} requires normalized config object resolution."
            ]

        entity = self._find_entity(config, selector, scope_path, (AddressObject, AddressGroup))
        if entity is None:
            return False, "unresolved address selector", [
                f"Address selector {selector!r} could not be resolved in scope {scope_path!r}."
            ]

        key = f"{entity.scope_path}/{entity.name}"
        if key in seen:
            return False, "recursive address group loop", [
                f"Address group recursion detected at {key}."
            ]
        seen.add(key)

        if isinstance(entity, AddressObject):
            return self._address_object_matches(entity, ip_value)

        if entity.dynamic_filter:
            return False, "dynamic address group not evaluated offline", [
                f"Dynamic address group {key} is not evaluated offline."
            ]

        warnings: list[str] = []
        details: list[str] = []
        matched = False
        for member in entity.members:
            member_match, member_detail, member_warnings = self._address_selector_matches(
                member, ip_value, entity.scope_path, config, seen=seen
            )
            warnings.extend(member_warnings)
            details.append(f"{member}: {member_detail}")
            matched = matched or member_match
        return matched, "; ".join(details), _dedupe(warnings)

    def _address_object_matches(
        self, address: AddressObject, ip_value: str
    ) -> tuple[bool, str, list[str]]:
        key = f"{address.scope_path}/{address.name}"
        if address.value is None:
            return False, "address object has no value", [f"Address object {key} has no value."]
        if address.address_kind == AddressKind.IP_NETMASK:
            try:
                network = ip_network(address.value, strict=False)
            except ValueError:
                return False, "invalid ip-netmask value", [
                    f"Address object {key} has invalid ip-netmask {address.value!r}."
                ]
            return ip_address(ip_value) in network, f"ip-netmask {network}", []
        if address.address_kind == AddressKind.IP_RANGE:
            try:
                start_raw, end_raw = address.value.split("-", maxsplit=1)
                ip = ip_address(ip_value)
                matched = ip_address(start_raw.strip()) <= ip <= ip_address(end_raw.strip())
            except ValueError:
                return False, "invalid ip-range value", [
                    f"Address object {key} has invalid ip-range {address.value!r}."
                ]
            return matched, f"ip-range {address.value}", []
        if address.address_kind == AddressKind.FQDN:
            return False, "fqdn object not resolved offline", [
                f"FQDN address object {key} is not resolved offline."
            ]
        return False, "unsupported address object type", [
            f"Address object {key} has unsupported type {address.address_kind}."
        ]

    def _application_match(self, application: str, applications: list[str]) -> _CriterionResult:
        if _is_any(applications):
            return _CriterionResult("application", True, "rule uses any")
        if application == "any":
            return _CriterionResult(
                "application",
                True,
                "explicit rule applications treated as possible match without App-ID hint",
                [
                    "Rule has explicit applications, but the test flow application is any; "
                    "offline App-ID classification is uncertain."
                ],
            )
        if application in applications:
            return _CriterionResult("application", True, f"{application!r} matched explicitly")
        return _CriterionResult("application", False, f"{application!r} is not in {applications!r}")

    def _service_match(
        self,
        test_case: PolicyTestCase,
        services: list[str],
        scope_path: str,
        config: NormalizedConfig | None,
    ) -> _CriterionResult:
        if _is_any(services):
            return _CriterionResult("service", True, "rule uses any")

        warnings: list[str] = []
        details: list[str] = []
        matched = False
        for selector in services:
            if selector == "application-default":
                # application-default depends on App-ID default ports maintained by PAN-OS content.
                # Ref: https://docs.paloaltonetworks.com/pan-os/11-0/pan-os-admin/app-id/application-default
                matched = True
                details.append("application-default: possible match")
                warnings.append(
                    "Rule uses application-default; offline matching cannot fully simulate App-ID "
                    "default port enforcement."
                )
                continue
            selector_match, selector_detail, selector_warnings = self._service_selector_matches(
                selector, test_case, scope_path, config, seen=set()
            )
            warnings.extend(selector_warnings)
            details.append(f"{selector}: {selector_detail}")
            matched = matched or selector_match

        return _CriterionResult("service", matched, "; ".join(details), _dedupe(warnings))

    def _service_selector_matches(
        self,
        selector: str,
        test_case: PolicyTestCase,
        scope_path: str,
        config: NormalizedConfig | None,
        *,
        seen: set[str],
    ) -> tuple[bool, str, list[str]]:
        if selector in _BUILTIN_SERVICES:
            protocol, destination = _BUILTIN_SERVICES[selector]
            matched = self._port_spec_matches(protocol, destination, None, test_case)
            return matched, f"built-in {protocol}/{destination}", []

        if config is None:
            return False, "object resolution unavailable without normalized config", [
                f"Service selector {selector!r} requires normalized config object resolution."
            ]

        entity = self._find_entity(config, selector, scope_path, (ServiceObject, ServiceGroup))
        if entity is None:
            return False, "unresolved service selector", [
                f"Service selector {selector!r} could not be resolved in scope {scope_path!r}."
            ]

        key = f"{entity.scope_path}/{entity.name}"
        if key in seen:
            return False, "recursive service group loop", [
                f"Service group recursion detected at {key}."
            ]
        seen.add(key)

        if isinstance(entity, ServiceObject):
            return self._service_object_matches(entity, test_case)

        warnings: list[str] = []
        details: list[str] = []
        matched = False
        for member in entity.members:
            member_match, member_detail, member_warnings = self._service_selector_matches(
                member, test_case, entity.scope_path, config, seen=seen
            )
            warnings.extend(member_warnings)
            details.append(f"{member}: {member_detail}")
            matched = matched or member_match
        return matched, "; ".join(details), _dedupe(warnings)

    def _service_object_matches(
        self, service: ServiceObject, test_case: PolicyTestCase
    ) -> tuple[bool, str, list[str]]:
        if test_case.destination_port is None:
            return False, "test flow has no destination port", [
                "Service matching requires a destination port for explicit service objects."
            ]
        warnings: list[str] = []
        details: list[str] = []
        matched = False
        for port in service.ports:
            if port.protocol == Protocol.UNKNOWN:
                warnings.append(
                    f"Service object {service.scope_path}/{service.name} has unsupported protocol."
                )
                continue
            try:
                port_match = self._service_port_matches(port, test_case)
            except ValueError as exc:
                warnings.append(
                    f"Service object {service.scope_path}/{service.name} has unsupported "
                    f"port syntax: {exc}."
                )
                continue
            details.append(f"{port.protocol.value}/{port.destination}: {port_match}")
            matched = matched or port_match
        return matched, "; ".join(details), _dedupe(warnings)

    def _service_port_matches(self, port: ServicePort, test_case: PolicyTestCase) -> bool:
        return self._port_spec_matches(
            port.protocol.value, port.destination, port.source, test_case
        )

    def _port_spec_matches(
        self,
        protocol: str,
        destination: str,
        source: str | None,
        test_case: PolicyTestCase,
    ) -> bool:
        if protocol != test_case.protocol or test_case.destination_port is None:
            return False
        if not _port_in_spec(test_case.destination_port, destination):
            return False
        if source and test_case.source_port is not None:
            return _port_in_spec(test_case.source_port, source)
        return source in {None, "", "1-65535"} or test_case.source_port is None

    def _user_match(self, user: str, users: list[str]) -> _CriterionResult:
        if _is_any(users):
            return _CriterionResult("user", True, "rule uses any")
        if user == "any":
            return _CriterionResult(
                "user",
                True,
                "explicit rule users treated as possible match without User-ID hint",
                [
                    "Rule has explicit users, but the test flow user is any; offline User-ID "
                    "mapping is uncertain."
                ],
            )
        if user in users:
            return _CriterionResult("user", True, f"{user!r} matched explicitly")
        return _CriterionResult("user", False, f"{user!r} is not in {users!r}")

    def _url_category_match(
        self, url_category: str | None, url_categories: list[str]
    ) -> _CriterionResult:
        if not url_categories or _is_any(url_categories):
            return _CriterionResult("url category", True, "rule uses any")
        if url_category in {None, "any"}:
            return _CriterionResult(
                "url category",
                True,
                "explicit URL categories treated as possible match without URL hint",
                [
                    "Rule has explicit URL categories, but the test flow has no URL category "
                    "hint; offline URL classification is uncertain."
                ],
            )
        if url_category in url_categories:
            return _CriterionResult(
                "url category", True, f"{url_category!r} matched explicitly"
            )
        return _CriterionResult(
            "url category", False, f"{url_category!r} is not in {url_categories!r}"
        )

    def _hip_match(self, test_case: PolicyTestCase, rule: SecurityRule) -> _CriterionResult:
        rule_hip = rule.metadata.get("hip_profiles")
        if not rule_hip:
            return _CriterionResult("hip", True, "rule has no parsed HIP criteria")
        if test_case.source_hip == "any" and test_case.destination_hip == "any":
            return _CriterionResult(
                "hip",
                True,
                "HIP criteria treated as possible match without HIP hints",
                ["Rule has HIP criteria, but offline HIP state is not evaluated in Phase 2."],
            )
        return _CriterionResult("hip", True, "HIP hint preserved but not deeply evaluated")

    def _rules_for_scope(
        self, config: NormalizedConfig, scope_path: str
    ) -> tuple[list[SecurityRule], list[str]]:
        scope = next((scope for scope in config.scopes if scope.path == scope_path), None)
        if scope is None:
            return [], [f"Scope {scope_path!r} does not exist in the imported configuration."]

        warnings: list[str] = []
        if scope.scope_type == ScopeType.VSYS:
            rules = [
                rule
                for rule in config.security_rules
                if rule.scope_path == scope_path
                and rule.rulebase_type == RulebaseType.SECURITY_LOCAL
            ]
            return sorted(rules, key=lambda rule: rule.position), warnings

        lineage = self._scope_lineage(config, scope_path)
        pre_order = list(reversed(lineage))
        post_order = lineage
        warnings.append(
            "Panorama Device Group test does not include local firewall rules that may be "
            "evaluated between pre-rules and post-rules."
        )

        # Panorama pre-rules evaluate above local firewall rules and post-rules evaluate below.
        # Ref: https://docs.paloaltonetworks.com/panorama/11-0/panorama-admin/panorama-overview/centralized-firewall-configuration-and-update-management/device-groups/device-group-policies
        ordered: list[SecurityRule] = []
        for pre_scope in pre_order:
            ordered.extend(self._rules_for_rulebase(config, pre_scope, RulebaseType.SECURITY_PRE))
        for post_scope in post_order:
            ordered.extend(self._rules_for_rulebase(config, post_scope, RulebaseType.SECURITY_POST))
        return ordered, warnings

    def _rules_for_rulebase(
        self, config: NormalizedConfig, scope_path: str, rulebase_type: RulebaseType
    ) -> list[SecurityRule]:
        return sorted(
            [
                rule
                for rule in config.security_rules
                if rule.scope_path == scope_path and rule.rulebase_type == rulebase_type
            ],
            key=lambda rule: rule.position,
        )

    def _scope_lineage(self, config: NormalizedConfig, scope_path: str) -> list[str]:
        scopes = {scope.path: scope for scope in config.scopes}
        lineage: list[str] = []
        current = scopes.get(scope_path)
        while current is not None:
            lineage.append(current.path)
            current = scopes.get(current.parent_path or "")
        if "shared" not in lineage and "shared" in scopes:
            lineage.append("shared")
        return lineage

    def _default_scope_path(self, config: NormalizedConfig) -> str | None:
        if config.security_rules:
            return config.security_rules[0].scope_path
        return config.scopes[0].path if config.scopes else None

    def _find_entity(
        self,
        config: NormalizedConfig,
        name: str,
        scope_path: str,
        entity_types: tuple[type[NormalizedEntity], ...],
    ) -> NormalizedEntity | None:
        lineage = self._scope_lineage(config, scope_path)
        for candidate_scope in lineage:
            for entity in config.entities:
                if (
                    entity.name == name
                    and entity.scope_path == candidate_scope
                    and isinstance(entity, entity_types)
                ):
                    return entity
        for entity in config.entities:
            if entity.name == name and isinstance(entity, entity_types):
                return entity
        return None


def _is_any(values: Iterable[str]) -> bool:
    return "any" in values


def _port_in_spec(port: int, spec: str) -> bool:
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start_raw, end_raw = part.split("-", maxsplit=1)
            if int(start_raw) <= port <= int(end_raw):
                return True
        elif int(part) == port:
            return True
    return False


def _dedupe(values: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(values))
