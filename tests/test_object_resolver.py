from __future__ import annotations

from frying_pan.analysis.dependencies import build_dependency_map


def test_dependency_resolver_scaffold_returns_empty_list() -> None:
    assert build_dependency_map() == []
