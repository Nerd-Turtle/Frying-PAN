from __future__ import annotations

from typing import TYPE_CHECKING

from frying_pan.analysis.references import extract_references
from frying_pan.normalized.references import Dependency

if TYPE_CHECKING:
    from frying_pan.normalized.config import NormalizedConfig


def build_dependency_map(config: NormalizedConfig | None = None) -> list[Dependency]:
    if config is None:
        return []

    return [
        Dependency(
            owner_scope_path=reference.owner_scope_path,
            owner_name=reference.owner_name,
            owner_type=reference.owner_type,
            target_name=reference.target_name,
            reference_kind=reference.reference_kind,
            target_type_hints=reference.target_type_hints,
            scope_context=reference.scope_context,
            resolved=reference.resolved,
            warnings=reference.warnings,
        )
        for reference in extract_references(config)
    ]
