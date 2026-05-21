from __future__ import annotations

from pathlib import Path

from lxml import etree

from frying_pan.analysis.dependencies import build_dependency_map
from frying_pan.analysis.references import extract_references
from frying_pan.normalized.addresses import AddressGroup, AddressKind, AddressObject
from frying_pan.normalized.config import NormalizedConfig
from frying_pan.normalized.entity import NormalizedEntity
from frying_pan.normalized.objects import Tag
from frying_pan.normalized.rules import RuleAction, Rulebase, RulebaseType, SecurityRule
from frying_pan.normalized.scope import ConfigScope, ScopeType
from frying_pan.normalized.services import Protocol, ServiceGroup, ServiceObject, ServicePort
from frying_pan.sources.base import SourceAdapter, SourceConfig, SourceType


class PanoramaXmlAdapter(SourceAdapter):
    source_type = SourceType.PANORAMA_XML

    def parse(self, source: SourceConfig) -> NormalizedConfig:
        path = _source_path(source)
        parser = etree.XMLParser(resolve_entities=False, no_network=True, recover=False)
        root = etree.parse(str(path), parser).getroot()

        scopes: list[ConfigScope] = []
        entities: list[NormalizedEntity] = []
        security_rules: list[SecurityRule] = []
        warnings: list[str] = []

        shared = root.find("shared")
        if shared is not None:
            shared_scope = ConfigScope(name="shared", scope_type=ScopeType.SHARED, path="shared")
            scopes.append(shared_scope)
            entities.extend(_parse_object_scope(shared, shared_scope.path, warnings))

        parent_lookup = _device_group_parent_lookup(root)
        for device_group in root.xpath(
            "./devices/entry[@name='localhost.localdomain']/device-group/entry"
        ):
            name = _entry_name(device_group)
            scope_path = f"device-group/{name}"
            parent_name = parent_lookup.get(name)
            scope = ConfigScope(
                name=name,
                scope_type=ScopeType.DEVICE_GROUP,
                path=scope_path,
                parent_path=f"device-group/{parent_name}" if parent_name else None,
            )
            scopes.append(scope)
            entities.extend(_parse_object_scope(device_group, scope_path, warnings))
            security_rules.extend(_parse_security_rules(device_group, scope_path))

        if not scopes:
            warnings.append("No Panorama shared or Device Group scopes were found.")

        _attach_source_metadata(source, scopes, entities, security_rules)
        config = NormalizedConfig(
            source_id=source.id,
            source_type=source.source_type,
            scopes=scopes,
            entities=entities,
            rulebases=_build_rulebases(security_rules),
            security_rules=security_rules,
            warnings=warnings,
        )
        config.references = extract_references(config)
        config.dependencies = build_dependency_map(config)
        return config


def _source_path(source: SourceConfig) -> Path:
    return source.workspace_path or source.original_path


def _entry_name(element: etree._Element) -> str:
    return element.get("name") or ""


def _text(element: etree._Element, path: str) -> str | None:
    value = element.findtext(path)
    return value.strip() if value and value.strip() else None


def _members(element: etree._Element, path: str) -> list[str]:
    return [
        member.text.strip()
        for member in element.findall(path)
        if member.text and member.text.strip()
    ]


def _base_metadata(element: etree._Element) -> dict[str, object]:
    metadata: dict[str, object] = {"source_line": element.sourceline}
    description = _text(element, "description")
    if description:
        metadata["description"] = description
    tags = _members(element, "tag/member")
    if tags:
        metadata["tags"] = tags
    return metadata


def _attach_source_metadata(
    source: SourceConfig,
    scopes: list[ConfigScope],
    entities: list[NormalizedEntity],
    security_rules: list[SecurityRule],
) -> None:
    scopes_by_path = {scope.path: scope for scope in scopes}
    for item in [*entities, *security_rules]:
        scope = scopes_by_path.get(item.scope_path)
        item.metadata.update(
            {
                "source_id": source.id,
                "source_type": source.source_type.value,
                "scope_name": scope.name if scope else item.scope_path,
                "scope_type": scope.scope_type.value if scope else None,
                "raw_xml_path": f"{item.scope_path}/{item.entity_type.value}/{item.name}",
            }
        )


def _device_group_parent_lookup(root: etree._Element) -> dict[str, str]:
    parents: dict[str, str] = {}
    for entry in root.xpath(
        "./readonly/devices/entry[@name='localhost.localdomain']/device-group/entry"
    ):
        parent = _text(entry, "parent-dg")
        if parent:
            parents[_entry_name(entry)] = parent
    return parents


def _parse_object_scope(
    scope_element: etree._Element, scope_path: str, warnings: list[str]
) -> list[NormalizedEntity]:
    entities: list[NormalizedEntity] = []

    entities.extend(_parse_address_objects(scope_element, scope_path, warnings))
    entities.extend(_parse_address_groups(scope_element, scope_path, warnings))
    entities.extend(_parse_service_objects(scope_element, scope_path, warnings))
    entities.extend(_parse_service_groups(scope_element, scope_path))
    entities.extend(_parse_tags(scope_element, scope_path))

    return entities


def _parse_address_objects(
    scope_element: etree._Element, scope_path: str, warnings: list[str]
) -> list[AddressObject]:
    objects: list[AddressObject] = []
    for entry in scope_element.findall("address/entry"):
        kind = AddressKind.UNKNOWN
        value = None
        for candidate in (AddressKind.IP_NETMASK, AddressKind.IP_RANGE, AddressKind.FQDN):
            value = _text(entry, candidate.value)
            if value:
                kind = candidate
                break
        if kind == AddressKind.UNKNOWN:
            warnings.append(
                f"Address object {scope_path}/{_entry_name(entry)} has unsupported type."
            )
        objects.append(
            AddressObject(
                name=_entry_name(entry),
                scope_path=scope_path,
                address_kind=kind,
                value=value,
                metadata=_base_metadata(entry),
            )
        )
    return objects


def _parse_address_groups(
    scope_element: etree._Element, scope_path: str, warnings: list[str]
) -> list[AddressGroup]:
    groups: list[AddressGroup] = []
    for entry in scope_element.findall("address-group/entry"):
        dynamic_filter = _text(entry, "dynamic/filter")
        if dynamic_filter:
            warnings.append(
                f"Dynamic address group {scope_path}/{_entry_name(entry)} filter is preserved "
                "but not evaluated."
            )
        groups.append(
            AddressGroup(
                name=_entry_name(entry),
                scope_path=scope_path,
                members=_members(entry, "static/member"),
                dynamic_filter=dynamic_filter,
                metadata=_base_metadata(entry),
            )
        )
    return groups


def _parse_service_objects(
    scope_element: etree._Element, scope_path: str, warnings: list[str]
) -> list[ServiceObject]:
    services: list[ServiceObject] = []
    for entry in scope_element.findall("service/entry"):
        ports: list[ServicePort] = []
        for protocol in (Protocol.TCP, Protocol.UDP):
            protocol_element = entry.find(f"protocol/{protocol.value}")
            if protocol_element is None:
                continue
            destination = _text(protocol_element, "port")
            if destination:
                ports.append(
                    ServicePort(
                        protocol=protocol,
                        destination=destination,
                        source=_text(protocol_element, "source-port"),
                    )
                )
        if not ports:
            warnings.append(
                f"Service object {scope_path}/{_entry_name(entry)} has unsupported protocol."
            )
        services.append(
            ServiceObject(
                name=_entry_name(entry),
                scope_path=scope_path,
                ports=ports,
                metadata=_base_metadata(entry),
            )
        )
    return services


def _parse_service_groups(scope_element: etree._Element, scope_path: str) -> list[ServiceGroup]:
    return [
        ServiceGroup(
            name=_entry_name(entry),
            scope_path=scope_path,
            members=_members(entry, "members/member"),
            metadata=_base_metadata(entry),
        )
        for entry in scope_element.findall("service-group/entry")
    ]


def _parse_tags(scope_element: etree._Element, scope_path: str) -> list[Tag]:
    tags: list[Tag] = []
    for entry in scope_element.findall("tag/entry"):
        metadata = _base_metadata(entry)
        comments = _text(entry, "comments")
        if comments:
            metadata["comments"] = comments
        tags.append(
            Tag(
                name=_entry_name(entry),
                scope_path=scope_path,
                color=_text(entry, "color"),
                metadata=metadata,
            )
        )
    return tags


def _parse_security_rules(scope_element: etree._Element, scope_path: str) -> list[SecurityRule]:
    rules: list[SecurityRule] = []
    rulebases = (
        ("pre-rulebase/security/rules/entry", RulebaseType.SECURITY_PRE),
        ("post-rulebase/security/rules/entry", RulebaseType.SECURITY_POST),
    )
    for xpath, rulebase_type in rulebases:
        for position, entry in enumerate(scope_element.findall(xpath), start=1):
            metadata = _base_metadata(entry)
            metadata.update(
                {
                    "disabled": _text(entry, "disabled") == "yes",
                    "log_start": _text(entry, "log-start"),
                    "log_end": _text(entry, "log-end"),
                }
            )
            profile_group = _members(entry, "profile-setting/group/member")
            if profile_group:
                metadata["profile_groups"] = profile_group
            rules.append(
                SecurityRule(
                    name=_entry_name(entry),
                    scope_path=scope_path,
                    rulebase_type=rulebase_type,
                    position=position,
                    source_zones=_members(entry, "from/member") or ["any"],
                    destination_zones=_members(entry, "to/member") or ["any"],
                    source_addresses=_members(entry, "source/member") or ["any"],
                    destination_addresses=_members(entry, "destination/member") or ["any"],
                    users=_members(entry, "source-user/member") or ["any"],
                    url_categories=_members(entry, "category/member"),
                    applications=_members(entry, "application/member") or ["any"],
                    services=_members(entry, "service/member") or ["any"],
                    action=_rule_action(_text(entry, "action")),
                    metadata=metadata,
                )
            )
    return rules


def _build_rulebases(security_rules: list[SecurityRule]) -> list[Rulebase]:
    grouped: dict[tuple[str, RulebaseType], list[SecurityRule]] = {}
    for rule in security_rules:
        grouped.setdefault((rule.scope_path, rule.rulebase_type), []).append(rule)
    return [
        Rulebase(scope_path=scope_path, rulebase_type=rulebase_type, security_rules=rules)
        for (scope_path, rulebase_type), rules in grouped.items()
    ]


def _rule_action(value: str | None) -> RuleAction:
    if value is None:
        return RuleAction.UNKNOWN
    try:
        return RuleAction(value)
    except ValueError:
        return RuleAction.UNKNOWN
