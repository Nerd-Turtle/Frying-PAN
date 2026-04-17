from __future__ import annotations

import hashlib
import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field


class PanoramaXmlParserError(ValueError):
    """Raised when Panorama XML cannot be parsed into the canonical inventory."""


@dataclass(frozen=True)
class ScopeRecord:
    scope_type: str
    scope_name: str
    scope_path: str
    parent_scope_path: str | None
    readonly_id: str | None
    metadata: dict


@dataclass(frozen=True)
class ObjectRecord:
    scope_path: str
    object_type: str
    object_name: str
    source_xpath: str
    raw_payload: dict
    normalized_payload: dict
    normalized_hash: str
    parse_status: str = "parsed"


@dataclass(frozen=True)
class ParseWarningRecord:
    warning_type: str
    message: str
    source_xpath: str | None
    scope_path: str | None = None
    details: dict = field(default_factory=dict)


@dataclass(frozen=True)
class ExtractedReferenceRecord:
    owner_scope_path: str
    owner_object_type: str
    owner_object_name: str
    reference_kind: str
    reference_path: str
    target_name: str
    target_type_hints: list[str]
    target_scope_hint: str | None = None
    metadata: dict = field(default_factory=dict)


@dataclass(frozen=True)
class PanoramaParseResult:
    scopes: list[ScopeRecord]
    objects: list[ObjectRecord]
    references: list[ExtractedReferenceRecord]
    warnings: list[ParseWarningRecord]


class PanoramaXmlParser:
    """Parse Panorama XML into canonical scope and object inventory records."""

    SUPPORTED_SCOPE_SECTIONS = {
        "address",
        "address-group",
        "service",
        "service-group",
        "tag",
    }
    IGNORED_SCOPE_SECTIONS = {"description", "devices"}

    def parse(self, xml_bytes: bytes) -> PanoramaParseResult:
        try:
            root = ET.fromstring(xml_bytes)
        except ET.ParseError as exc:
            raise PanoramaXmlParserError(f"Invalid Panorama XML: {exc}") from exc

        scopes: list[ScopeRecord] = []
        objects: list[ObjectRecord] = []
        references: list[ExtractedReferenceRecord] = []
        warnings: list[ParseWarningRecord] = []

        readonly_meta = self._parse_readonly_device_groups(root)

        shared_element = root.find("./shared")
        if shared_element is None:
            raise PanoramaXmlParserError("Panorama XML is missing the /config/shared section.")

        shared_scope = ScopeRecord(
            scope_type="shared",
            scope_name="shared",
            scope_path="shared",
            parent_scope_path=None,
            readonly_id=None,
            metadata={"source_xpath": "/config/shared"},
        )
        scopes.append(shared_scope)
        shared_objects, shared_warnings = self._parse_scope_inventory(
            scope=shared_scope,
            scope_element=shared_element,
            scope_xpath="/config/shared",
        )
        objects.extend(shared_objects)
        references.extend(self._extract_scope_references(shared_scope, shared_element))
        warnings.extend(shared_warnings)

        device_entry = root.find("./devices/entry")
        if device_entry is not None:
            warnings.extend(self._parse_device_root_warnings(device_entry))

            device_group_parent = device_entry.find("./device-group")
            if device_group_parent is not None:
                device_group_entries = device_group_parent.findall("./entry")
                scopes.extend(
                    self._build_device_group_scopes(
                        entries=device_group_entries,
                        readonly_meta=readonly_meta,
                    )
                )
                scope_lookup = {
                    scope.scope_name: scope
                    for scope in scopes
                    if scope.scope_type == "device_group"
                }
                for dg_entry in device_group_entries:
                    scope = scope_lookup.get(dg_entry.get("name", ""))
                    if scope is None:
                        continue
                    dg_objects, dg_warnings = self._parse_scope_inventory(
                        scope=scope,
                        scope_element=dg_entry,
                        scope_xpath=self._device_group_xpath(scope.scope_name),
                    )
                    objects.extend(dg_objects)
                    references.extend(self._extract_scope_references(scope, dg_entry))
                    warnings.extend(dg_warnings)

        return PanoramaParseResult(
            scopes=scopes,
            objects=objects,
            references=references,
            warnings=warnings,
        )

    def _build_device_group_scopes(
        self,
        entries: list[ET.Element],
        readonly_meta: dict[str, dict[str, str | None]],
    ) -> list[ScopeRecord]:
        entries_by_name = {
            entry.get("name", ""): entry for entry in entries if entry.get("name")
        }
        order_lookup = {entry.get("name", ""): index for index, entry in enumerate(entries)}

        children_by_parent: dict[str | None, list[str]] = {}
        for name in entries_by_name:
            parent_name = readonly_meta.get(name, {}).get("parent_dg")
            children_by_parent.setdefault(parent_name, []).append(name)

        for child_names in children_by_parent.values():
            child_names.sort(key=lambda child_name: order_lookup.get(child_name, 0))

        scope_records: list[ScopeRecord] = []

        def visit(name: str, parent_scope_path: str | None) -> None:
            entry = entries_by_name[name]
            parent_name = readonly_meta.get(name, {}).get("parent_dg")
            scope_parent_path = parent_scope_path or "shared"
            scope_path = f"{scope_parent_path}/device-group:{name}"
            description = self._text(entry.find("./description"))
            scope_records.append(
                ScopeRecord(
                    scope_type="device_group",
                    scope_name=name,
                    scope_path=scope_path,
                    parent_scope_path=scope_parent_path if parent_name else "shared",
                    readonly_id=readonly_meta.get(name, {}).get("id"),
                    metadata={
                        "description": description,
                        "parent_dg": parent_name,
                        "source_xpath": self._device_group_xpath(name),
                    },
                )
            )
            for child_name in children_by_parent.get(name, []):
                visit(child_name, scope_path)

        for top_level_name in children_by_parent.get(None, []):
            visit(top_level_name, None)

        return scope_records

    def _parse_readonly_device_groups(
        self, root: ET.Element
    ) -> dict[str, dict[str, str | None]]:
        result: dict[str, dict[str, str | None]] = {}
        for entry in root.findall("./readonly/devices/entry/device-group/entry"):
            name = entry.get("name")
            if not name:
                continue
            result[name] = {
                "id": self._text(entry.find("./id")),
                "parent_dg": self._text(entry.find("./parent-dg")),
            }
        return result

    def _parse_device_root_warnings(self, device_entry: ET.Element) -> list[ParseWarningRecord]:
        warnings: list[ParseWarningRecord] = []
        for section_name in ("template", "template-stack"):
            if device_entry.find(f"./{section_name}") is None:
                continue
            warnings.append(
                ParseWarningRecord(
                    warning_type="unsupported_root_section",
                    message=(
                        f"Unsupported root section '{section_name}' was skipped during "
                        "v1 inventory parsing."
                    ),
                    source_xpath=(
                        f"/config/devices/entry[@name='{device_entry.get('name', 'unknown')}']/"
                        f"{section_name}"
                    ),
                    details={"section_name": section_name},
                )
            )
        return warnings

    def _parse_scope_inventory(
        self,
        scope: ScopeRecord,
        scope_element: ET.Element,
        scope_xpath: str,
    ) -> tuple[list[ObjectRecord], list[ParseWarningRecord]]:
        objects: list[ObjectRecord] = []
        warnings: list[ParseWarningRecord] = []

        for child in list(scope_element):
            child_name = self._tag_name(child.tag)

            if child_name in self.SUPPORTED_SCOPE_SECTIONS:
                objects.extend(
                    self._parse_supported_section(
                        scope=scope,
                        section_element=child,
                        section_name=child_name,
                        section_xpath=f"{scope_xpath}/{child_name}",
                    )
                )
                continue

            if child_name in self.IGNORED_SCOPE_SECTIONS:
                continue

            warnings.append(
                ParseWarningRecord(
                    warning_type="unsupported_scope_section",
                    message=(
                        f"Unsupported scope section '{child_name}' was skipped during "
                        "v1 inventory parsing."
                    ),
                    source_xpath=f"{scope_xpath}/{child_name}",
                    scope_path=scope.scope_path,
                    details={
                        "scope_name": scope.scope_name,
                        "scope_type": scope.scope_type,
                        "section_name": child_name,
                    },
                )
            )

        return objects, warnings

    def _parse_supported_section(
        self,
        scope: ScopeRecord,
        section_element: ET.Element,
        section_name: str,
        section_xpath: str,
    ) -> list[ObjectRecord]:
        records: list[ObjectRecord] = []
        for entry in section_element.findall("./entry"):
            name = entry.get("name")
            if not name:
                continue

            object_xpath = f"{section_xpath}/entry[@name='{name}']"
            raw_payload, normalized_payload = self._build_payloads(section_name, entry)
            records.append(
                ObjectRecord(
                    scope_path=scope.scope_path,
                    object_type=section_name.replace("-", "_"),
                    object_name=name,
                    source_xpath=object_xpath,
                    raw_payload=raw_payload,
                    normalized_payload=normalized_payload,
                    normalized_hash=self._payload_hash(normalized_payload),
                )
            )
        return records

    def _extract_scope_references(
        self, scope: ScopeRecord, scope_element: ET.Element
    ) -> list[ExtractedReferenceRecord]:
        references: list[ExtractedReferenceRecord] = []

        for entry in scope_element.findall("./address-group/entry"):
            name = entry.get("name")
            if not name:
                continue
            for index, member in enumerate(entry.findall("./static/member"), start=1):
                references.append(
                    ExtractedReferenceRecord(
                        owner_scope_path=scope.scope_path,
                        owner_object_type="address_group",
                        owner_object_name=name,
                        reference_kind="group_member",
                        reference_path=f"static/member[{index}]",
                        target_name=self._text(member) or "",
                        target_type_hints=["address", "address_group"],
                    )
                )

        for entry in scope_element.findall("./service-group/entry"):
            name = entry.get("name")
            if not name:
                continue
            for index, member in enumerate(entry.findall("./members/member"), start=1):
                references.append(
                    ExtractedReferenceRecord(
                        owner_scope_path=scope.scope_path,
                        owner_object_type="service_group",
                        owner_object_name=name,
                        reference_kind="group_member",
                        reference_path=f"members/member[{index}]",
                        target_name=self._text(member) or "",
                        target_type_hints=[
                            "service",
                            "service_group",
                            "builtin_service",
                        ],
                    )
                )

        return references

    def _build_payloads(self, section_name: str, entry: ET.Element) -> tuple[dict, dict]:
        if section_name == "address":
            return self._parse_address_payload(entry)
        if section_name == "address-group":
            return self._parse_address_group_payload(entry)
        if section_name == "service":
            return self._parse_service_payload(entry)
        if section_name == "service-group":
            return self._parse_service_group_payload(entry)
        if section_name == "tag":
            return self._parse_tag_payload(entry)
        raise PanoramaXmlParserError(f"Unsupported section '{section_name}' passed to payload parser.")

    def _parse_address_payload(self, entry: ET.Element) -> tuple[dict, dict]:
        value_node = next((child for child in list(entry) if self._text(child) is not None), None)
        value_kind = self._tag_name(value_node.tag) if value_node is not None else "unknown"
        value = self._text(value_node) or ""
        raw_payload = {"value_kind": value_kind, "value": value}
        normalized_payload = {"value_kind": value_kind, "address_text": value}
        if value_kind in {"ip-netmask", "ip-range", "ip-wildcard"}:
            normalized_payload["ip_version"] = 6 if ":" in value else 4
        return raw_payload, normalized_payload

    def _parse_address_group_payload(self, entry: ET.Element) -> tuple[dict, dict]:
        static_members = [self._text(member) or "" for member in entry.findall("./static/member")]
        dynamic_filter = self._text(entry.find("./dynamic/filter"))
        if static_members:
            raw_payload = {"group_kind": "static", "members": static_members}
            normalized_payload = {"group_kind": "static", "members_ordered": static_members}
        elif dynamic_filter:
            raw_payload = {"group_kind": "dynamic", "filter": dynamic_filter}
            normalized_payload = {"group_kind": "dynamic", "filter": dynamic_filter}
        else:
            raw_payload = {"group_kind": "empty", "members": []}
            normalized_payload = {"group_kind": "empty", "members_ordered": []}
        return raw_payload, normalized_payload

    def _parse_service_payload(self, entry: ET.Element) -> tuple[dict, dict]:
        protocol_node = entry.find("./protocol/tcp")
        protocol_name = "tcp"
        if protocol_node is None:
            protocol_node = entry.find("./protocol/udp")
            protocol_name = "udp"

        port = self._text(protocol_node.find("./port")) if protocol_node is not None else None
        source_port = (
            self._text(protocol_node.find("./source-port")) if protocol_node is not None else None
        )
        override = None
        if protocol_node is not None and protocol_node.find("./override/no") is not None:
            override = "no"

        raw_payload = {
            "protocol": protocol_name if protocol_node is not None else "unknown",
            "port": port,
            "source_port": source_port,
            "override": override,
        }
        normalized_payload = {
            "protocol": protocol_name if protocol_node is not None else "unknown",
            "destination_port": port,
            "source_port": source_port,
            "override": override,
        }
        return raw_payload, normalized_payload

    def _parse_service_group_payload(self, entry: ET.Element) -> tuple[dict, dict]:
        members = [self._text(member) or "" for member in entry.findall("./members/member")]
        raw_payload = {"members": members}
        normalized_payload = {"members_ordered": members}
        return raw_payload, normalized_payload

    def _parse_tag_payload(self, entry: ET.Element) -> tuple[dict, dict]:
        color = self._text(entry.find("./color"))
        raw_payload = {"color": color}
        normalized_payload = {"color": color}
        return raw_payload, normalized_payload

    def _device_group_xpath(self, device_group_name: str) -> str:
        return (
            "/config/devices/entry[@name='localhost.localdomain']"
            f"/device-group/entry[@name='{device_group_name}']"
        )

    def _payload_hash(self, payload: dict) -> str:
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def _text(self, element: ET.Element | None) -> str | None:
        if element is None or element.text is None:
            return None
        return element.text.strip()

    def _tag_name(self, tag: str) -> str:
        return tag.split("}", 1)[-1]
