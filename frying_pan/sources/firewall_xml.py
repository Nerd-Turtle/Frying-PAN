from __future__ import annotations

from lxml import etree

from frying_pan.analysis.dependencies import build_dependency_map
from frying_pan.analysis.references import extract_references
from frying_pan.normalized.config import NormalizedConfig
from frying_pan.normalized.entity import NormalizedEntity
from frying_pan.normalized.rules import RulebaseType, SecurityRule
from frying_pan.normalized.scope import ConfigScope, ScopeType
from frying_pan.sources.base import SourceAdapter, SourceConfig, SourceType
from frying_pan.sources.panorama_xml import (
    _attach_source_metadata,
    _base_metadata,
    _build_rulebases,
    _entry_name,
    _members,
    _parse_object_scope,
    _rule_action,
    _source_path,
    _text,
)


class FirewallXmlAdapter(SourceAdapter):
    source_type = SourceType.FIREWALL_XML

    def parse(self, source: SourceConfig) -> NormalizedConfig:
        path = _source_path(source)
        parser = etree.XMLParser(resolve_entities=False, no_network=True, recover=False)
        root = etree.parse(str(path), parser).getroot()

        scopes: list[ConfigScope] = []
        entities: list[NormalizedEntity] = []
        security_rules: list[SecurityRule] = []
        warnings: list[str] = []

        for vsys in root.xpath("./devices/entry[@name='localhost.localdomain']/vsys/entry"):
            name = _entry_name(vsys)
            scope_path = f"vsys/{name}"
            scopes.append(ConfigScope(name=name, scope_type=ScopeType.VSYS, path=scope_path))
            entities.extend(_parse_object_scope(vsys, scope_path, warnings))
            security_rules.extend(_parse_local_security_rules(vsys, scope_path))

        if not scopes:
            warnings.append("No firewall vsys scopes were found.")

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


def _parse_local_security_rules(
    scope_element: etree._Element, scope_path: str
) -> list[SecurityRule]:
    rules: list[SecurityRule] = []
    for position, entry in enumerate(
        scope_element.findall("rulebase/security/rules/entry"), start=1
    ):
        metadata = _base_metadata(entry)
        metadata.update(
            {
                "disabled": _text(entry, "disabled") == "yes",
                "log_start": _text(entry, "log-start"),
                "log_end": _text(entry, "log-end"),
            }
        )
        rules.append(
            SecurityRule(
                name=_entry_name(entry),
                scope_path=scope_path,
                rulebase_type=RulebaseType.SECURITY_LOCAL,
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
