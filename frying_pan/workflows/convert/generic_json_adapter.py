from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from frying_pan.analysis.dependencies import build_dependency_map
from frying_pan.analysis.references import extract_references
from frying_pan.normalized.addresses import AddressGroup, AddressKind, AddressObject
from frying_pan.normalized.config import NormalizedConfig
from frying_pan.normalized.entity import NormalizedEntity
from frying_pan.normalized.objects import Tag
from frying_pan.normalized.rules import RuleAction, Rulebase, RulebaseType, SecurityRule
from frying_pan.normalized.scope import ConfigScope, ScopeType
from frying_pan.normalized.services import Protocol, ServiceGroup, ServiceObject, ServicePort
from frying_pan.normalized.vendor_metadata import ConversionWarning, UnsupportedFeature
from frying_pan.sources.base import SourceType
from frying_pan.workflows.convert.adapter_contract import ConversionAdapter
from frying_pan.workflows.convert.converted_import import (
    ConversionPackageValidation,
    ConvertedImportPackage,
)


class GenericJsonConversionAdapter(ConversionAdapter):
    source_format = "generic-json"

    def can_parse(self, path: Path) -> bool:
        return path.suffix.lower() == ".json"

    def convert(self, path: Path) -> ConvertedImportPackage:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("Generic JSON conversion input must be a JSON object.")
        warnings: list[ConversionWarning] = []
        unsupported: list[UnsupportedFeature] = []
        scopes = _parse_scopes(data.get("scopes", []), warnings)
        entities = _parse_entities(data, warnings, unsupported)
        security_rules = _parse_rules(data.get("security_rules", []), warnings, unsupported)
        source_metadata = (
            data.get("metadata", {}) if isinstance(data.get("metadata"), dict) else {}
        )
        config = NormalizedConfig(
            source_id=str(data.get("source_id") or path.stem),
            source_type=SourceType.NORMALIZED_IMPORT_FUTURE,
            scopes=scopes,
            entities=entities,
            security_rules=security_rules,
            rulebases=_build_rulebases(security_rules),
            warnings=[warning.message for warning in warnings],
        )
        config.references = extract_references(config)
        config.dependencies = build_dependency_map(config)
        package = ConvertedImportPackage(
            name=str(data.get("name") or path.stem),
            source_format=self.source_format,
            source_path=str(path),
            source_metadata=source_metadata,
            normalized_config=config,
            warnings=warnings,
            unsupported_features=unsupported,
        )
        package.validation = validate_conversion_package(package)
        return package


def validate_conversion_package(package: ConvertedImportPackage) -> ConversionPackageValidation:
    errors: list[str] = []
    warnings: list[str] = []
    if not package.normalized_config.scopes:
        errors.append("Converted package must include at least one scope.")
    duplicate_entity_keys: set[tuple[str, str, str]] = set()
    for entity in package.normalized_config.entities:
        key = (entity.scope_path, entity.entity_type.value, entity.name)
        if key in duplicate_entity_keys:
            errors.append(f"Duplicate converted entity {key}.")
        duplicate_entity_keys.add(key)
    unresolved = [ref for ref in package.normalized_config.references if not ref.resolved]
    if unresolved:
        warnings.append(f"{len(unresolved)} converted references are unresolved.")
    if package.unsupported_features:
        warnings.append(f"{len(package.unsupported_features)} unsupported features require review.")
    return ConversionPackageValidation(errors=errors, warnings=warnings)


def _parse_scopes(
    items: list[dict[str, Any]], warnings: list[ConversionWarning]
) -> list[ConfigScope]:
    scopes: list[ConfigScope] = []
    for index, item in enumerate(items):
        try:
            scope_type = ScopeType(item.get("scope_type", "synthetic_vendor"))
        except ValueError:
            scope_type = ScopeType.SYNTHETIC_VENDOR
            warnings.append(
                _warning("unsupported_scope_type", f"Unsupported scope type at {index}.")
            )
        name = str(item.get("name") or item.get("path") or f"scope-{index}")
        path = str(item.get("path") or name)
        scopes.append(
            ConfigScope(
                name=name,
                scope_type=scope_type,
                path=path,
                parent_path=item.get("parent_path"),
            )
        )
    return scopes


def _parse_entities(
    data: dict[str, Any],
    warnings: list[ConversionWarning],
    unsupported: list[UnsupportedFeature],
) -> list[NormalizedEntity]:
    entities: list[NormalizedEntity] = []
    for item in data.get("addresses", []):
        try:
            kind = AddressKind(item.get("type", "ip-netmask"))
        except ValueError:
            kind = AddressKind.UNKNOWN
            unsupported.append(
                UnsupportedFeature(
                    feature="address_type",
                    source_location=str(item.get("name")),
                    notes=f"Unsupported address type {item.get('type')!r}.",
                )
            )
        entities.append(
            AddressObject(
                name=str(item["name"]),
                scope_path=str(item.get("scope_path", "shared")),
                address_kind=kind,
                value=item.get("value"),
                metadata=_metadata(item),
            )
        )
    for item in data.get("address_groups", []):
        dynamic_filter = item.get("dynamic_filter")
        if dynamic_filter:
            warnings.append(
                _warning(
                    "dynamic_address_group",
                    "Dynamic address group filter preserved but not evaluated.",
                    source_location=str(item.get("name")),
                )
            )
        entities.append(
            AddressGroup(
                name=str(item["name"]),
                scope_path=str(item.get("scope_path", "shared")),
                members=[str(member) for member in item.get("members", [])],
                dynamic_filter=dynamic_filter,
                metadata=_metadata(item),
            )
        )
    for item in data.get("services", []):
        protocol_value = item.get("protocol", "tcp")
        try:
            protocol = Protocol(protocol_value)
        except ValueError:
            protocol = Protocol.UNKNOWN
            unsupported.append(
                UnsupportedFeature(
                    feature="service_protocol",
                    source_location=str(item.get("name")),
                    notes=f"Unsupported service protocol {protocol_value!r}.",
                )
            )
        entities.append(
            ServiceObject(
                name=str(item["name"]),
                scope_path=str(item.get("scope_path", "shared")),
                ports=[
                    ServicePort(
                        protocol=protocol,
                        destination=str(item.get("destination", "")),
                        source=item.get("source"),
                    )
                ],
                metadata=_metadata(item),
            )
        )
    for item in data.get("service_groups", []):
        entities.append(
            ServiceGroup(
                name=str(item["name"]),
                scope_path=str(item.get("scope_path", "shared")),
                members=[str(member) for member in item.get("members", [])],
                metadata=_metadata(item),
            )
        )
    for item in data.get("tags", []):
        entities.append(
            Tag(
                name=str(item["name"]),
                scope_path=str(item.get("scope_path", "shared")),
                color=item.get("color"),
                metadata=_metadata(item),
            )
        )
    return entities


def _parse_rules(
    items: list[dict[str, Any]],
    warnings: list[ConversionWarning],
    unsupported: list[UnsupportedFeature],
) -> list[SecurityRule]:
    rules: list[SecurityRule] = []
    for position, item in enumerate(items, start=1):
        try:
            action = RuleAction(item.get("action", "unknown"))
        except ValueError:
            action = RuleAction.UNKNOWN
            unsupported.append(
                UnsupportedFeature(
                    feature="rule_action",
                    source_location=str(item.get("name")),
                    notes=f"Unsupported rule action {item.get('action')!r}.",
                )
            )
        try:
            rulebase_type = RulebaseType(item.get("rulebase_type", "security_local"))
        except ValueError:
            rulebase_type = RulebaseType.SECURITY_LOCAL
            warnings.append(
                _warning(
                    "unsupported_rulebase_type",
                    "Unsupported rulebase type defaulted to security_local.",
                    source_location=str(item.get("name")),
                )
            )
        metadata = _metadata(item)
        if item.get("unsupported_criteria"):
            unsupported.append(
                UnsupportedFeature(
                    feature="rule_criteria",
                    source_location=str(item.get("name")),
                    notes="Unsupported rule criteria were preserved as metadata.",
                )
            )
            metadata["unsupported_criteria"] = item.get("unsupported_criteria")
        rules.append(
            SecurityRule(
                name=str(item["name"]),
                scope_path=str(item.get("scope_path", "shared")),
                rulebase_type=rulebase_type,
                position=int(item.get("position", position)),
                source_zones=_list(item.get("source_zones")) or ["any"],
                destination_zones=_list(item.get("destination_zones")) or ["any"],
                source_addresses=_list(item.get("source_addresses")) or ["any"],
                destination_addresses=_list(item.get("destination_addresses")) or ["any"],
                applications=_list(item.get("applications")) or ["any"],
                services=_list(item.get("services")) or ["any"],
                users=_list(item.get("users")) or ["any"],
                url_categories=_list(item.get("url_categories")),
                action=action,
                metadata=metadata,
            )
        )
    return sorted(
        rules, key=lambda rule: (rule.scope_path, rule.rulebase_type.value, rule.position)
    )


def _build_rulebases(rules: list[SecurityRule]) -> list[Rulebase]:
    grouped: dict[tuple[str, RulebaseType], list[SecurityRule]] = {}
    for rule in rules:
        grouped.setdefault((rule.scope_path, rule.rulebase_type), []).append(rule)
    return [
        Rulebase(scope_path=scope_path, rulebase_type=rulebase_type, security_rules=rules)
        for (scope_path, rulebase_type), rules in grouped.items()
    ]


def _list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def _metadata(item: dict[str, Any]) -> dict[str, Any]:
    metadata = item.get("metadata")
    return metadata if isinstance(metadata, dict) else {}


def _warning(
    code: str, message: str, source_location: str | None = None
) -> ConversionWarning:
    return ConversionWarning(code=code, message=message, source_location=source_location)
