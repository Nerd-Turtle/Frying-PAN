from __future__ import annotations

import ipaddress
from datetime import datetime, timezone
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.config_object import ConfigObject
from app.models.config_reference import ConfigReference
from app.models.scope import Scope
from app.schemas.analysis import (
    AnalysisFilters,
    AnalysisObjectRef,
    DuplicateFinding,
    NormalizationSuggestion,
    ProjectAnalysisReport,
    PromotionAssessment,
)


PROMOTABLE_OBJECT_TYPES = {
    "address",
    "address_group",
    "service",
    "service_group",
    "tag",
}


def generate_project_analysis_report(
    db: Session, project_id: str, filters: AnalysisFilters
) -> ProjectAnalysisReport:
    objects = _load_objects(db=db, project_id=project_id, filters=filters)

    return ProjectAnalysisReport(
        generated_at=datetime.now(timezone.utc),
        filters=filters,
        duplicate_name_findings=_build_duplicate_name_findings(objects),
        duplicate_value_findings=_build_duplicate_value_findings(objects),
        normalization_suggestions=_build_normalization_suggestions(objects),
        promotion_candidates=_build_promotion_assessments(objects, include_status="candidate"),
        promotion_blockers=_build_promotion_assessments(objects, include_status="blocked"),
    )


def _load_objects(
    db: Session, project_id: str, filters: AnalysisFilters
) -> list[ConfigObject]:
    statement = (
        select(ConfigObject)
        .join(Scope, ConfigObject.scope_id == Scope.id)
        .where(ConfigObject.project_id == project_id)
        .options(
            selectinload(ConfigObject.scope),
            selectinload(ConfigObject.outgoing_references).selectinload(
                ConfigReference.resolved_object
            ),
        )
        .order_by(Scope.scope_path, ConfigObject.object_type, ConfigObject.object_name)
    )

    if filters.source_id:
        statement = statement.where(ConfigObject.source_id == filters.source_id)
    if filters.object_type:
        statement = statement.where(ConfigObject.object_type == filters.object_type)
    if filters.scope_path:
        statement = statement.where(Scope.scope_path == filters.scope_path)

    return list(db.scalars(statement).all())


def _build_duplicate_name_findings(objects: list[ConfigObject]) -> list[DuplicateFinding]:
    grouped: dict[tuple[str, str], list[ConfigObject]] = defaultdict(list)
    for obj in objects:
        grouped[(obj.object_type, obj.object_name)].append(obj)

    findings: list[DuplicateFinding] = []
    for (object_type, object_name), members in sorted(grouped.items()):
        if len(members) < 2:
            continue
        findings.append(
            DuplicateFinding(
                finding_kind="same_name",
                object_type=object_type,
                key=object_name,
                items=[_object_ref(member) for member in members],
            )
        )
    return findings


def _build_duplicate_value_findings(objects: list[ConfigObject]) -> list[DuplicateFinding]:
    grouped: dict[tuple[str, str | None], list[ConfigObject]] = defaultdict(list)
    for obj in objects:
        grouped[(obj.object_type, obj.normalized_hash)].append(obj)

    findings: list[DuplicateFinding] = []
    for (object_type, normalized_hash), members in sorted(grouped.items()):
        if normalized_hash is None or len(members) < 2:
            continue
        findings.append(
            DuplicateFinding(
                finding_kind="same_normalized_value",
                object_type=object_type,
                key=normalized_hash,
                normalized_payload=members[0].normalized_payload,
                items=[_object_ref(member) for member in members],
            )
        )
    return findings


def _build_normalization_suggestions(
    objects: list[ConfigObject],
) -> list[NormalizationSuggestion]:
    suggestions: list[NormalizationSuggestion] = []

    for obj in objects:
        if obj.object_type != "address":
            continue

        raw_value_kind = obj.raw_payload.get("value_kind")
        raw_value = obj.raw_payload.get("value")
        if raw_value_kind != "ip-netmask" or not isinstance(raw_value, str):
            continue
        if "/" in raw_value:
            continue

        suggested_value: str | None = None
        suggestion_kind: str | None = None
        try:
            ip_obj = ipaddress.ip_address(raw_value)
        except ValueError:
            continue

        if ip_obj.version == 4:
            suggested_value = f"{raw_value}/32"
            suggestion_kind = "host_ipv4_to_cidr"
        else:
            suggested_value = f"{raw_value}/128"
            suggestion_kind = "host_ipv6_to_cidr"

        suggestions.append(
            NormalizationSuggestion(
                object_id=obj.id,
                source_id=obj.source_id,
                scope_path=obj.scope.scope_path,
                object_type=obj.object_type,
                object_name=obj.object_name,
                kind=suggestion_kind,
                original_value=raw_value,
                suggested_value=suggested_value,
            )
        )

    return suggestions


def _build_promotion_assessments(
    objects: list[ConfigObject], include_status: str
) -> list[PromotionAssessment]:
    shared_lookup = {
        (obj.object_type, obj.object_name): obj
        for obj in objects
        if obj.scope.scope_path == "shared"
    }

    assessments: list[PromotionAssessment] = []

    for obj in objects:
        if obj.scope.scope_path == "shared":
            continue
        if obj.object_type not in PROMOTABLE_OBJECT_TYPES:
            continue

        blockers: list[str] = []
        notes: list[str] = []
        dependency_targets: list[str] = []
        dependency_scopes: set[str] = set()

        shared_object = shared_lookup.get((obj.object_type, obj.object_name))
        if shared_object is not None:
            if shared_object.normalized_hash == obj.normalized_hash:
                blockers.append("equivalent_object_exists_in_shared")
            else:
                blockers.append("name_collision_in_shared")

        for reference in obj.outgoing_references:
            dependency_targets.append(reference.target_name)
            resolved_scope = reference.metadata_json.get("resolved_scope_path")
            if reference.resolution_status == "resolved_local":
                blockers.append("depends_on_non_shared_object")
                if resolved_scope:
                    dependency_scopes.add(resolved_scope)
            elif reference.resolution_status == "resolved_in_ancestor":
                blockers.append("depends_on_ancestor_scope")
                if resolved_scope:
                    dependency_scopes.add(resolved_scope)
            elif reference.resolution_status in {"unresolved", "ambiguous"}:
                blockers.append(reference.resolution_status)
            elif reference.resolution_status == "resolved_in_shared":
                dependency_scopes.add("shared")
            elif reference.resolution_status == "builtin":
                dependency_scopes.add("builtin")

        mixed_scope_dependencies = (
            any(scope not in {"shared", "builtin"} for scope in dependency_scopes)
            and any(scope in {"shared", "builtin"} for scope in dependency_scopes)
        )
        if mixed_scope_dependencies:
            blockers.append("mixed_scope_dependencies")

        blockers = sorted(set(blockers))
        if not blockers:
            if not dependency_targets:
                notes.append("leaf_object")
            else:
                notes.append("dependencies_resolve_without_local_blockers")

        assessment = PromotionAssessment(
            object_id=obj.id,
            source_id=obj.source_id,
            scope_path=obj.scope.scope_path,
            object_type=obj.object_type,
            object_name=obj.object_name,
            status="blocked" if blockers else "candidate",
            blockers=blockers,
            dependency_targets=sorted(set(dependency_targets)),
            mixed_scope_dependencies=mixed_scope_dependencies,
            notes=notes,
        )

        if assessment.status == include_status:
            assessments.append(assessment)

    return assessments


def _object_ref(obj: ConfigObject) -> AnalysisObjectRef:
    return AnalysisObjectRef(
        id=obj.id,
        source_id=obj.source_id,
        scope_path=obj.scope.scope_path,
        object_type=obj.object_type,
        object_name=obj.object_name,
        normalized_hash=obj.normalized_hash,
        raw_payload=obj.raw_payload,
        normalized_payload=obj.normalized_payload,
    )
