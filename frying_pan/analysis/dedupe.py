from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from ipaddress import ip_address, ip_network
from typing import Any

from frying_pan.analysis.dedupe_models import (
    DedupeAnalysisResult,
    DedupeFinding,
    DedupeFindingType,
    DedupeSeverity,
    ObjectFingerprint,
)
from frying_pan.normalized.addresses import AddressGroup, AddressKind, AddressObject
from frying_pan.normalized.config import NormalizedConfig
from frying_pan.normalized.entity import NormalizedEntity
from frying_pan.normalized.objects import Tag
from frying_pan.normalized.services import Protocol, ServiceGroup, ServiceObject

_BUILTIN_TARGETS = {"", "any", "service-http", "service-https", "application-default"}


class DedupeAnalysisEngine:
    def analyze(self, config: NormalizedConfig) -> DedupeAnalysisResult:
        fingerprints = {
            _entity_key(entity): fingerprint_entity(entity) for entity in config.entities
        }
        findings: list[DedupeFinding] = []
        findings.extend(self._duplicate_findings(fingerprints))
        findings.extend(self._same_name_conflicts(fingerprints))
        findings.extend(self._unused_candidates(config, fingerprints))
        findings.extend(self._placement_recommendations(fingerprints))
        findings.extend(self._unsupported_findings(fingerprints))
        return DedupeAnalysisResult(
            source_id=config.source_id,
            source_type=config.source_type.value,
            analyzed_object_count=len(config.entities),
            findings=[
                finding.model_copy(update={"finding_id": f"DC-{index:04d}"})
                for index, finding in enumerate(findings, start=1)
            ],
            warnings=[
                "Unused object findings are candidates only; unparsed configuration sections "
                "may still reference objects."
            ],
        )

    def _duplicate_findings(
        self, fingerprints: dict[tuple[str, str, str], ObjectFingerprint]
    ) -> list[DedupeFinding]:
        grouped: dict[tuple[str, str], list[tuple[str, str, str]]] = defaultdict(list)
        for key, fingerprint in fingerprints.items():
            if fingerprint.warnings:
                continue
            grouped[(fingerprint.entity_type, fingerprint.fingerprint)].append(key)

        findings: list[DedupeFinding] = []
        for (entity_type, fingerprint), keys in grouped.items():
            if len(keys) < 2:
                continue
            findings.append(
                DedupeFinding(
                    finding_type=DedupeFindingType.DUPLICATE_OBJECT,
                    severity=DedupeSeverity.MEDIUM,
                    object_type=entity_type,
                    object_names=sorted({name for _, _, name in keys}),
                    scopes=sorted({scope for scope, _, _ in keys}),
                    fingerprints=[fingerprint],
                    explanation=(
                        "Multiple objects have the same normalized value and can be reviewed "
                        "as duplicate candidates."
                    ),
                    recommendation=(
                        "Review references before staging any dedupe action in a Modify or "
                        "Migrate plan."
                    ),
                )
            )
        return findings

    def _same_name_conflicts(
        self, fingerprints: dict[tuple[str, str, str], ObjectFingerprint]
    ) -> list[DedupeFinding]:
        grouped: dict[tuple[str, str], list[tuple[tuple[str, str, str], ObjectFingerprint]]] = (
            defaultdict(list)
        )
        for key, fingerprint in fingerprints.items():
            _, entity_type, name = key
            grouped[(entity_type, name)].append((key, fingerprint))

        findings: list[DedupeFinding] = []
        for (entity_type, name), entries in grouped.items():
            distinct = {fingerprint.fingerprint for _, fingerprint in entries}
            if len(entries) < 2 or len(distinct) < 2:
                continue
            scopes = sorted({scope for (scope, _, _), _ in entries})
            findings.append(
                DedupeFinding(
                    finding_type=DedupeFindingType.SAME_NAME_CONFLICT,
                    severity=DedupeSeverity.HIGH,
                    object_type=entity_type,
                    object_names=[name],
                    scopes=scopes,
                    fingerprints=sorted(distinct),
                    explanation=(
                        f"{name} appears in multiple scopes with different normalized values."
                    ),
                    recommendation=(
                        "Review Panorama inheritance and override behavior before staging any "
                        "rename, move, or merge action."
                    ),
                    warnings=[
                        "Panorama descendants can override ancestor objects; this finding is "
                        "scope-aware but does not prove runtime safety."
                    ],
                )
            )
        return findings

    def _unused_candidates(
        self,
        config: NormalizedConfig,
        fingerprints: dict[tuple[str, str, str], ObjectFingerprint],
    ) -> list[DedupeFinding]:
        referenced_names = {
            reference.target_name
            for reference in [*config.references, *config.dependencies]
            if reference.target_name not in _BUILTIN_TARGETS
        }
        findings: list[DedupeFinding] = []
        for scope_path, entity_type, name in sorted(fingerprints):
            if name in referenced_names:
                continue
            findings.append(
                DedupeFinding(
                    finding_type=DedupeFindingType.UNUSED_OBJECT_CANDIDATE,
                    severity=DedupeSeverity.LOW,
                    object_type=entity_type,
                    object_names=[name],
                    scopes=[scope_path],
                    fingerprints=[fingerprints[(scope_path, entity_type, name)].fingerprint],
                    explanation=(
                        f"{name} is not referenced by parsed rule/object dependency records."
                    ),
                    recommendation=(
                        "Review in Panorama before staging cleanup; parser coverage is not yet "
                        "global across every PAN-OS section."
                    ),
                    warnings=[
                        "Candidate only: unparsed configuration sections may still reference "
                        "this object."
                    ],
                )
            )
        return findings

    def _placement_recommendations(
        self, fingerprints: dict[tuple[str, str, str], ObjectFingerprint]
    ) -> list[DedupeFinding]:
        grouped: dict[tuple[str, str], list[tuple[str, str, str]]] = defaultdict(list)
        for key, fingerprint in fingerprints.items():
            if fingerprint.warnings:
                continue
            grouped[(fingerprint.entity_type, fingerprint.fingerprint)].append(key)

        findings: list[DedupeFinding] = []
        for (entity_type, fingerprint), keys in grouped.items():
            scopes = sorted({scope for scope, _, _ in keys})
            non_shared_scopes = [scope for scope in scopes if scope != "shared"]
            if len(non_shared_scopes) < 2 or "shared" in scopes:
                continue
            findings.append(
                DedupeFinding(
                    finding_type=DedupeFindingType.PLACEMENT_RECOMMENDATION,
                    severity=DedupeSeverity.INFO,
                    object_type=entity_type,
                    object_names=sorted({name for _, _, name in keys}),
                    scopes=scopes,
                    fingerprints=[fingerprint],
                    explanation=(
                        "Duplicate values appear in multiple non-shared scopes and may be "
                        "candidates for shared placement review."
                    ),
                    recommendation=(
                        "Consider whether a Shared or ancestor Device Group object would reduce "
                        "duplication before staging a Modify or Migrate action."
                    ),
                    warnings=[
                        "Recommendation only; object inheritance and overrides must be reviewed."
                    ],
                )
            )
        return findings

    def _unsupported_findings(
        self, fingerprints: dict[tuple[str, str, str], ObjectFingerprint]
    ) -> list[DedupeFinding]:
        findings: list[DedupeFinding] = []
        for scope_path, entity_type, name in sorted(fingerprints):
            fingerprint = fingerprints[(scope_path, entity_type, name)]
            if not fingerprint.warnings:
                continue
            findings.append(
                DedupeFinding(
                    finding_type=DedupeFindingType.UNSUPPORTED_OBJECT,
                    severity=DedupeSeverity.LOW,
                    object_type=entity_type,
                    object_names=[name],
                    scopes=[scope_path],
                    fingerprints=[fingerprint.fingerprint],
                    explanation=f"{name} could not be fully fingerprinted for dedupe analysis.",
                    recommendation="Review manually before relying on dedupe/conflict findings.",
                    warnings=fingerprint.warnings,
                )
            )
        return findings


def fingerprint_entity(entity: NormalizedEntity) -> ObjectFingerprint:
    comparable, warnings = _comparable_entity(entity)
    payload = {
        "entity_type": entity.entity_type.value,
        "comparable": comparable,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return ObjectFingerprint(
        entity_type=entity.entity_type.value,
        fingerprint=hashlib.sha256(encoded.encode("utf-8")).hexdigest(),
        comparable=comparable,
        warnings=warnings,
    )


def find_duplicate_objects(config: NormalizedConfig | None = None) -> list[DedupeFinding]:
    if config is None:
        return []
    return [
        finding
        for finding in DedupeAnalysisEngine().analyze(config).findings
        if finding.finding_type == DedupeFindingType.DUPLICATE_OBJECT
    ]


def _comparable_entity(entity: NormalizedEntity) -> tuple[dict[str, Any], list[str]]:
    if isinstance(entity, AddressObject):
        return _address_object_comparable(entity)
    if isinstance(entity, AddressGroup):
        warnings = []
        if entity.dynamic_filter:
            warnings.append(
                f"Dynamic address group {entity.scope_path}/{entity.name} is not evaluated."
            )
        return {
            "kind": "address-group",
            "members": sorted(entity.members),
            "dynamic_filter": entity.dynamic_filter,
        }, warnings
    if isinstance(entity, ServiceObject):
        return _service_object_comparable(entity)
    if isinstance(entity, ServiceGroup):
        return {"kind": "service-group", "members": sorted(entity.members)}, []
    if isinstance(entity, Tag):
        return {"kind": "tag", "color": entity.color}, []
    return {"kind": entity.entity_type.value, "name": entity.name}, [
        f"{entity.entity_type.value} fingerprinting is not fully supported."
    ]


def _address_object_comparable(address: AddressObject) -> tuple[dict[str, Any], list[str]]:
    warnings: list[str] = []
    value = address.value or ""
    normalized_value = value
    if address.address_kind == AddressKind.IP_NETMASK and value:
        try:
            normalized_value = str(ip_network(value, strict=False))
        except ValueError:
            warnings.append(f"Invalid ip-netmask value {value!r}.")
    elif address.address_kind == AddressKind.IP_RANGE and value:
        try:
            start, end = value.split("-", maxsplit=1)
            normalized_value = f"{ip_address(start.strip())}-{ip_address(end.strip())}"
        except ValueError:
            warnings.append(f"Invalid ip-range value {value!r}.")
    elif address.address_kind == AddressKind.FQDN:
        normalized_value = value.lower()
    elif address.address_kind == AddressKind.UNKNOWN:
        warnings.append("Unsupported address object kind.")
    return {
        "kind": address.address_kind.value,
        "value": normalized_value,
    }, warnings


def _service_object_comparable(service: ServiceObject) -> tuple[dict[str, Any], list[str]]:
    warnings: list[str] = []
    ports = []
    for port in service.ports:
        if port.protocol == Protocol.UNKNOWN:
            warnings.append("Unsupported service protocol.")
        ports.append(
            {
                "protocol": port.protocol.value,
                "destination": _normalize_port_spec(port.destination, warnings),
                "source": _normalize_port_spec(port.source, warnings) if port.source else None,
            }
        )
    return {"kind": "service", "ports": sorted(ports, key=json.dumps)}, warnings


def _normalize_port_spec(spec: str, warnings: list[str]) -> str:
    normalized_parts: list[str] = []
    for raw_part in spec.split(","):
        part = raw_part.strip()
        if not part:
            continue
        try:
            if "-" in part:
                start, end = part.split("-", maxsplit=1)
                normalized_parts.append(f"{int(start)}-{int(end)}")
            else:
                normalized_parts.append(str(int(part)))
        except ValueError:
            warnings.append(f"Unsupported service port syntax {part!r}.")
            normalized_parts.append(part)
    return ",".join(sorted(normalized_parts))


def _entity_key(entity: NormalizedEntity) -> tuple[str, str, str]:
    return (entity.scope_path, entity.entity_type.value, entity.name)
