from __future__ import annotations

import ipaddress
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.config_object import ConfigObject
from app.models.config_reference import ConfigReference


PROMOTABLE_OBJECT_TYPES = {
    "address",
    "address_group",
    "service",
    "service_group",
    "tag",
}


@dataclass(frozen=True)
class NormalizationSelectionRecord:
    object_id: str
    kind: str


@dataclass(frozen=True)
class MergePreviewPlan:
    preview_summary: dict
    operations_payload: dict


class MergeWorkbench:
    """
    Backend-owned merge preview and change planning.

    The workbench plans change intent only. It does not mutate imported state.
    """

    def preview(
        self,
        db: Session,
        project_id: str,
        selected_object_ids: list[str],
        selected_normalizations: list[NormalizationSelectionRecord],
    ) -> MergePreviewPlan:
        objects = self._load_objects(db=db, project_id=project_id)
        object_by_id = {obj.id: obj for obj in objects}
        shared_lookup = {
            (obj.object_type, obj.object_name): obj
            for obj in objects
            if obj.scope.scope_path == "shared"
        }

        planned_object_ids: set[str] = set()
        blocked_objects: dict[str, dict] = {}
        object_operations: list[dict] = []
        visited: set[str] = set()

        for object_id in selected_object_ids:
            obj = object_by_id.get(object_id)
            if obj is None:
                continue
            self._plan_object_promotion(
                obj=obj,
                shared_lookup=shared_lookup,
                planned_object_ids=planned_object_ids,
                blocked_objects=blocked_objects,
                object_operations=object_operations,
                visited=visited,
            )

        reference_rewrites = self._build_reference_rewrites(
            db=db,
            promoted_object_ids=planned_object_ids,
        )

        normalization_operations = self._build_normalization_operations(
            object_by_id=object_by_id,
            selected_normalizations=selected_normalizations,
        )

        operations_payload = {
            "selected_object_ids": selected_object_ids,
            "selected_normalizations": [
                {"object_id": item.object_id, "kind": item.kind}
                for item in selected_normalizations
            ],
            "object_operations": object_operations,
            "reference_rewrites": reference_rewrites,
            "normalization_operations": normalization_operations,
            "blocked_objects": list(blocked_objects.values()),
        }
        preview_summary = {
            "planned_object_count": len(object_operations),
            "reference_rewrite_count": len(reference_rewrites),
            "normalization_count": len(normalization_operations),
            "blocked_object_count": len(blocked_objects),
        }
        return MergePreviewPlan(
            preview_summary=preview_summary,
            operations_payload=operations_payload,
        )

    def _load_objects(self, db: Session, project_id: str) -> list[ConfigObject]:
        statement = (
            select(ConfigObject)
            .where(ConfigObject.project_id == project_id)
            .options(
                selectinload(ConfigObject.scope),
                selectinload(ConfigObject.outgoing_references).selectinload(
                    ConfigReference.resolved_object
                ).selectinload(ConfigObject.scope),
            )
        )
        return list(db.scalars(statement).all())

    def _plan_object_promotion(
        self,
        obj: ConfigObject,
        shared_lookup: dict[tuple[str, str], ConfigObject],
        planned_object_ids: set[str],
        blocked_objects: dict[str, dict],
        object_operations: list[dict],
        visited: set[str],
    ) -> bool:
        if obj.id in visited:
            return obj.id in planned_object_ids
        visited.add(obj.id)

        blockers: list[str] = []
        dependency_targets: list[str] = []
        dependency_ids: list[str] = []

        if obj.scope.scope_path == "shared":
            blockers.append("already_in_shared")
        if obj.object_type not in PROMOTABLE_OBJECT_TYPES:
            blockers.append("unsupported_object_type")

        shared_collision = shared_lookup.get((obj.object_type, obj.object_name))
        if shared_collision is not None:
            if shared_collision.normalized_hash == obj.normalized_hash:
                blockers.append("equivalent_object_exists_in_shared")
            else:
                blockers.append("name_collision_in_shared")

        if not blockers:
            for reference in obj.outgoing_references:
                dependency_targets.append(reference.target_name)
                if reference.resolution_status in {"builtin", "resolved_in_shared"}:
                    continue
                if reference.resolution_status in {"unresolved", "ambiguous"}:
                    blockers.append(reference.resolution_status)
                    continue

                resolved_object = reference.resolved_object
                if resolved_object is None:
                    blockers.append("missing_resolved_target")
                    continue
                dependency_ids.append(resolved_object.id)

                dependency_ok = self._plan_object_promotion(
                    obj=resolved_object,
                    shared_lookup=shared_lookup,
                    planned_object_ids=planned_object_ids,
                    blocked_objects=blocked_objects,
                    object_operations=object_operations,
                    visited=visited,
                )
                if not dependency_ok:
                    blockers.append(f"blocked_dependency:{resolved_object.object_name}")

        blockers = sorted(set(blockers))
        if blockers:
            blocked_objects[obj.id] = {
                "object_id": obj.id,
                "object_name": obj.object_name,
                "object_type": obj.object_type,
                "scope_path": obj.scope.scope_path,
                "blockers": blockers,
                "dependency_targets": sorted(set(dependency_targets)),
            }
            return False

        if obj.id not in planned_object_ids:
            planned_object_ids.add(obj.id)
            object_operations.append(
                {
                    "operation": "promote_to_shared",
                    "object_id": obj.id,
                    "object_name": obj.object_name,
                    "object_type": obj.object_type,
                    "from_scope_path": obj.scope.scope_path,
                    "to_scope_path": "shared",
                    "dependency_object_ids": sorted(set(dependency_ids)),
                    "reason": "selected_or_required_dependency",
                }
            )
        return True

    def _build_reference_rewrites(
        self, db: Session, promoted_object_ids: set[str]
    ) -> list[dict]:
        if not promoted_object_ids:
            return []

        statement = (
            select(ConfigReference)
            .where(ConfigReference.resolved_object_id.in_(promoted_object_ids))
            .options(
                selectinload(ConfigReference.owner_object).selectinload(ConfigObject.scope),
                selectinload(ConfigReference.resolved_object).selectinload(ConfigObject.scope),
            )
        )
        rewrites: list[dict] = []
        for reference in db.scalars(statement).all():
            owner_object = reference.owner_object
            resolved_object = reference.resolved_object
            if owner_object is None or resolved_object is None:
                continue
            current_scope = reference.metadata_json.get("resolved_scope_path")
            if current_scope == "shared":
                continue
            rewrites.append(
                {
                    "operation": "rewrite_reference_resolution",
                    "reference_id": reference.id,
                    "owner_object_id": owner_object.id,
                    "owner_object_name": owner_object.object_name,
                    "owner_scope_path": owner_object.scope.scope_path,
                    "reference_path": reference.reference_path,
                    "target_name": reference.target_name,
                    "from_resolved_scope_path": current_scope,
                    "to_resolved_scope_path": "shared",
                    "target_object_id": resolved_object.id,
                }
            )
        return rewrites

    def _build_normalization_operations(
        self,
        object_by_id: dict[str, ConfigObject],
        selected_normalizations: list[NormalizationSelectionRecord],
    ) -> list[dict]:
        operations: list[dict] = []
        for selection in selected_normalizations:
            obj = object_by_id.get(selection.object_id)
            if obj is None or obj.object_type != "address":
                continue

            raw_value_kind = obj.raw_payload.get("value_kind")
            raw_value = obj.raw_payload.get("value")
            if raw_value_kind != "ip-netmask" or not isinstance(raw_value, str) or "/" in raw_value:
                continue

            try:
                ip_obj = ipaddress.ip_address(raw_value)
            except ValueError:
                continue

            if ip_obj.version == 4 and selection.kind == "host_ipv4_to_cidr":
                suggested_value = f"{raw_value}/32"
            elif ip_obj.version == 6 and selection.kind == "host_ipv6_to_cidr":
                suggested_value = f"{raw_value}/128"
            else:
                continue

            operations.append(
                {
                    "operation": "normalize_object_value",
                    "object_id": obj.id,
                    "object_name": obj.object_name,
                    "object_type": obj.object_type,
                    "scope_path": obj.scope.scope_path,
                    "kind": selection.kind,
                    "from_value": raw_value,
                    "to_value": suggested_value,
                }
            )
        return operations
