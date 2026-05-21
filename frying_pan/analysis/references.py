from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING

from frying_pan.normalized.addresses import AddressGroup
from frying_pan.normalized.entity import EntityType, NormalizedEntity
from frying_pan.normalized.references import Reference, ReferenceKind
from frying_pan.normalized.rules import SecurityRule
from frying_pan.normalized.services import ServiceGroup

if TYPE_CHECKING:
    from frying_pan.normalized.config import NormalizedConfig

IGNORED_TARGETS = {"", "any"}


def extract_references(config: NormalizedConfig) -> list[Reference]:
    entity_index = _build_entity_index(config.entities)
    references: list[Reference] = []

    for entity in config.entities:
        references.extend(_entity_references(entity, entity_index))

    for rule in config.security_rules:
        references.extend(_rule_references(rule, entity_index))

    return references


def _entity_references(
    entity: NormalizedEntity, entity_index: set[tuple[str, str]]
) -> list[Reference]:
    references: list[Reference] = []

    if isinstance(entity, AddressGroup):
        references.extend(
            _references_for_targets(
                owner=entity,
                targets=entity.members,
                reference_kind=ReferenceKind.ADDRESS_GROUP_MEMBER,
                target_type_hints=[
                    EntityType.ADDRESS_OBJECT.value,
                    EntityType.ADDRESS_GROUP.value,
                ],
                entity_index=entity_index,
            )
        )

    if isinstance(entity, ServiceGroup):
        references.extend(
            _references_for_targets(
                owner=entity,
                targets=entity.members,
                reference_kind=ReferenceKind.SERVICE_GROUP_MEMBER,
                target_type_hints=[
                    EntityType.SERVICE_OBJECT.value,
                    EntityType.SERVICE_GROUP.value,
                ],
                entity_index=entity_index,
            )
        )

    references.extend(
        _references_for_targets(
            owner=entity,
            targets=_metadata_list(entity.metadata.get("tags")),
            reference_kind=ReferenceKind.TAG,
            target_type_hints=[EntityType.TAG.value],
            entity_index=entity_index,
        )
    )

    return references


def _rule_references(
    rule: SecurityRule, entity_index: set[tuple[str, str]]
) -> list[Reference]:
    references: list[Reference] = []
    targets_by_kind: tuple[tuple[ReferenceKind, Iterable[str], list[str]], ...] = (
        (ReferenceKind.RULE_SOURCE_ZONE, rule.source_zones, [EntityType.ZONE.value]),
        (ReferenceKind.RULE_DESTINATION_ZONE, rule.destination_zones, [EntityType.ZONE.value]),
        (
            ReferenceKind.RULE_SOURCE_ADDRESS,
            rule.source_addresses,
            [EntityType.ADDRESS_OBJECT.value, EntityType.ADDRESS_GROUP.value],
        ),
        (
            ReferenceKind.RULE_DESTINATION_ADDRESS,
            rule.destination_addresses,
            [EntityType.ADDRESS_OBJECT.value, EntityType.ADDRESS_GROUP.value],
        ),
        (ReferenceKind.RULE_APPLICATION, rule.applications, ["application", "application_group"]),
        (
            ReferenceKind.RULE_SERVICE,
            rule.services,
            [EntityType.SERVICE_OBJECT.value, EntityType.SERVICE_GROUP.value],
        ),
        (ReferenceKind.RULE_URL_CATEGORY, rule.url_categories, ["url_category"]),
        (
            ReferenceKind.RULE_PROFILE_GROUP,
            _metadata_list(rule.metadata.get("profile_groups")),
            ["profile_group"],
        ),
        (ReferenceKind.TAG, _metadata_list(rule.metadata.get("tags")), [EntityType.TAG.value]),
    )

    for reference_kind, targets, target_type_hints in targets_by_kind:
        references.extend(
            _references_for_targets(
                owner=rule,
                targets=targets,
                reference_kind=reference_kind,
                target_type_hints=target_type_hints,
                entity_index=entity_index,
            )
        )

    return references


def _references_for_targets(
    *,
    owner: NormalizedEntity,
    targets: Iterable[str],
    reference_kind: ReferenceKind,
    target_type_hints: list[str],
    entity_index: set[tuple[str, str]],
) -> list[Reference]:
    references: list[Reference] = []
    for target in targets:
        if target in IGNORED_TARGETS:
            continue
        resolved = _target_exists(owner.scope_path, target, entity_index)
        warnings = [] if resolved else [f"Unresolved reference to {target!r}."]
        references.append(
            Reference(
                owner_scope_path=owner.scope_path,
                owner_name=owner.name,
                owner_type=owner.entity_type.value,
                target_name=target,
                reference_kind=reference_kind,
                target_type_hints=target_type_hints,
                scope_context=owner.scope_path,
                resolved=resolved,
                warnings=warnings,
            )
        )
    return references


def _build_entity_index(entities: list[NormalizedEntity]) -> set[tuple[str, str]]:
    return {(entity.scope_path, entity.name) for entity in entities}


def _target_exists(
    owner_scope_path: str,
    target_name: str,
    entity_index: set[tuple[str, str]],
) -> bool:
    return (
        (owner_scope_path, target_name) in entity_index
        or ("shared", target_name) in entity_index
    )


def _metadata_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str)]
    return []
