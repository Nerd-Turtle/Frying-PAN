from __future__ import annotations

from frying_pan.normalized.objects import Tag


def normalize_tag(name: str, scope_path: str, color: str | None = None) -> Tag:
    return Tag(name=name, scope_path=scope_path, color=color)
