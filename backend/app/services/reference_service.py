from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.parsers.panorama_xml import (
    ExtractedReferenceRecord,
    ObjectRecord,
    ScopeRecord,
)


BUILTIN_SERVICES = {
    "any",
    "application-default",
    "service-http",
    "service-https",
}


@dataclass(frozen=True)
class ReferenceResolutionSettings:
    device_group_precedence: Literal["local_first", "ancestor_first"] = "local_first"


@dataclass(frozen=True)
class ResolvedReferenceRecord:
    owner_scope_path: str
    owner_object_type: str
    owner_object_name: str
    reference_kind: str
    reference_path: str
    target_name: str
    target_type_hints: list[str]
    target_scope_hint: str | None
    resolution_status: str
    resolved_scope_path: str | None
    resolved_object_type: str | None
    resolved_object_name: str | None
    resolved_builtin_key: str | None = None
    metadata: dict | None = None


def resolve_references(
    scopes: list[ScopeRecord],
    objects: list[ObjectRecord],
    references: list[ExtractedReferenceRecord],
    settings: ReferenceResolutionSettings | None = None,
) -> list[ResolvedReferenceRecord]:
    settings = settings or ReferenceResolutionSettings()

    scope_by_path = {scope.scope_path: scope for scope in scopes}
    object_lookup: dict[tuple[str, str], list[ObjectRecord]] = {}
    for obj in objects:
        object_lookup.setdefault((obj.scope_path, obj.object_name), []).append(obj)

    resolved_records: list[ResolvedReferenceRecord] = []
    for reference in references:
        stages = _resolution_stages(
            owner_scope_path=reference.owner_scope_path,
            scope_by_path=scope_by_path,
            settings=settings,
        )

        resolved_record: ResolvedReferenceRecord | None = None
        for stage_name, scope_paths in stages:
            candidates = _matching_candidates(
                object_lookup=object_lookup,
                scope_paths=scope_paths,
                target_name=reference.target_name,
                target_type_hints=reference.target_type_hints,
            )
            if not candidates:
                continue

            if len(candidates) > 1:
                resolved_record = ResolvedReferenceRecord(
                    owner_scope_path=reference.owner_scope_path,
                    owner_object_type=reference.owner_object_type,
                    owner_object_name=reference.owner_object_name,
                    reference_kind=reference.reference_kind,
                    reference_path=reference.reference_path,
                    target_name=reference.target_name,
                    target_type_hints=reference.target_type_hints,
                    target_scope_hint=reference.target_scope_hint,
                    resolution_status="ambiguous",
                    resolved_scope_path=None,
                    resolved_object_type=None,
                    resolved_object_name=None,
                    metadata={
                        "candidate_scopes": [candidate.scope_path for candidate in candidates],
                        "candidate_types": [candidate.object_type for candidate in candidates],
                    },
                )
                break

            candidate = candidates[0]
            resolved_record = ResolvedReferenceRecord(
                owner_scope_path=reference.owner_scope_path,
                owner_object_type=reference.owner_object_type,
                owner_object_name=reference.owner_object_name,
                reference_kind=reference.reference_kind,
                reference_path=reference.reference_path,
                target_name=reference.target_name,
                target_type_hints=reference.target_type_hints,
                target_scope_hint=reference.target_scope_hint,
                resolution_status=stage_name,
                resolved_scope_path=candidate.scope_path,
                resolved_object_type=candidate.object_type,
                resolved_object_name=candidate.object_name,
                metadata={},
            )
            break

        if resolved_record is None:
            builtin_key = _resolve_builtin(reference.target_name, reference.target_type_hints)
            if builtin_key is not None:
                resolved_record = ResolvedReferenceRecord(
                    owner_scope_path=reference.owner_scope_path,
                    owner_object_type=reference.owner_object_type,
                    owner_object_name=reference.owner_object_name,
                    reference_kind=reference.reference_kind,
                    reference_path=reference.reference_path,
                    target_name=reference.target_name,
                    target_type_hints=reference.target_type_hints,
                    target_scope_hint=reference.target_scope_hint,
                    resolution_status="builtin",
                    resolved_scope_path=None,
                    resolved_object_type=None,
                    resolved_object_name=None,
                    resolved_builtin_key=builtin_key,
                    metadata={},
                )
            else:
                resolved_record = ResolvedReferenceRecord(
                    owner_scope_path=reference.owner_scope_path,
                    owner_object_type=reference.owner_object_type,
                    owner_object_name=reference.owner_object_name,
                    reference_kind=reference.reference_kind,
                    reference_path=reference.reference_path,
                    target_name=reference.target_name,
                    target_type_hints=reference.target_type_hints,
                    target_scope_hint=reference.target_scope_hint,
                    resolution_status="unresolved",
                    resolved_scope_path=None,
                    resolved_object_type=None,
                    resolved_object_name=None,
                    metadata={},
                )

        resolved_records.append(resolved_record)

    return resolved_records


def _resolution_stages(
    owner_scope_path: str,
    scope_by_path: dict[str, ScopeRecord],
    settings: ReferenceResolutionSettings,
) -> list[tuple[str, list[str]]]:
    if owner_scope_path == "shared":
        return [("resolved_local", ["shared"])]

    ancestor_paths: list[str] = []
    current_path = owner_scope_path
    while True:
        scope = scope_by_path[current_path]
        parent_scope_path = scope.parent_scope_path
        if parent_scope_path in (None, "shared"):
            break
        ancestor_paths.append(parent_scope_path)
        current_path = parent_scope_path

    ancestor_stages = [("resolved_in_ancestor", [ancestor_path]) for ancestor_path in ancestor_paths]

    if settings.device_group_precedence == "ancestor_first":
        return [
            *ancestor_stages,
            ("resolved_local", [owner_scope_path]),
            ("resolved_in_shared", ["shared"]),
        ]

    return [
        ("resolved_local", [owner_scope_path]),
        *ancestor_stages,
        ("resolved_in_shared", ["shared"]),
    ]


def _matching_candidates(
    object_lookup: dict[tuple[str, str], list[ObjectRecord]],
    scope_paths: list[str],
    target_name: str,
    target_type_hints: list[str],
) -> list[ObjectRecord]:
    if not scope_paths:
        return []

    allowed_types = {hint for hint in target_type_hints if not hint.startswith("builtin_")}
    candidates: list[ObjectRecord] = []
    for scope_path in scope_paths:
        for obj in object_lookup.get((scope_path, target_name), []):
            if obj.object_type in allowed_types:
                candidates.append(obj)
    return candidates


def _resolve_builtin(target_name: str, target_type_hints: list[str]) -> str | None:
    if "builtin_service" in target_type_hints and target_name in BUILTIN_SERVICES:
        return target_name
    return None
