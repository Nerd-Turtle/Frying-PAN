from __future__ import annotations

from frying_pan.analysis.conflicts import detect_conflicts
from frying_pan.analysis.dedupe import find_duplicate_objects
from frying_pan.analysis.unused import find_unused_candidates


def test_analysis_scaffolds_are_explicitly_empty() -> None:
    assert detect_conflicts() == []
    assert find_duplicate_objects() == []
    assert find_unused_candidates() == []
