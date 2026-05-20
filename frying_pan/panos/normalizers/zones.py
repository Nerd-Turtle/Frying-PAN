from __future__ import annotations

from frying_pan.normalized.objects import Zone


def normalize_zone(name: str, scope_path: str) -> Zone:
    return Zone(name=name, scope_path=scope_path)
