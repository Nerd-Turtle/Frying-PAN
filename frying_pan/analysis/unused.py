from __future__ import annotations

from frying_pan.analysis.dedupe import DedupeAnalysisEngine
from frying_pan.analysis.dedupe_models import DedupeFinding, DedupeFindingType
from frying_pan.normalized.config import NormalizedConfig


def find_unused_candidates(config: NormalizedConfig | None = None) -> list[DedupeFinding]:
    if config is None:
        return []
    return [
        finding
        for finding in DedupeAnalysisEngine().analyze(config).findings
        if finding.finding_type == DedupeFindingType.UNUSED_OBJECT_CANDIDATE
    ]
