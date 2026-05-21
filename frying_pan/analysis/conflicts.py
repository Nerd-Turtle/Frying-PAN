from __future__ import annotations

from frying_pan.analysis.dedupe import DedupeAnalysisEngine
from frying_pan.analysis.dedupe_models import DedupeFinding, DedupeFindingType
from frying_pan.normalized.config import NormalizedConfig
from frying_pan.normalized.references import Conflict


def detect_conflicts(
    config: NormalizedConfig | None = None,
) -> list[Conflict] | list[DedupeFinding]:
    if config is None:
        return []
    return [
        finding
        for finding in DedupeAnalysisEngine().analyze(config).findings
        if finding.finding_type == DedupeFindingType.SAME_NAME_CONFLICT
    ]
