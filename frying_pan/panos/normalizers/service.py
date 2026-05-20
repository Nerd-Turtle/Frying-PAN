from __future__ import annotations

from frying_pan.normalized.services import ServiceObject


def normalize_service_object(name: str, scope_path: str) -> ServiceObject:
    # TODO: Normalize protocol and port ranges.
    return ServiceObject(name=name, scope_path=scope_path)
