from __future__ import annotations

from pathlib import Path

from frying_pan.analysis.dedupe import DedupeAnalysisEngine
from frying_pan.export.dedupe_report_exporter import (
    export_dedupe_analysis_markdown,
    render_dedupe_analysis_markdown,
)
from frying_pan.normalized.addresses import AddressKind, AddressObject
from frying_pan.normalized.config import NormalizedConfig
from frying_pan.sources.base import SourceType


def test_dedupe_analysis_markdown_report(tmp_path: Path) -> None:
    config = NormalizedConfig(
        source_id="source-1",
        source_type=SourceType.FIREWALL_XML,
        entities=[
            AddressObject(
                name="a",
                scope_path="vsys/vsys1",
                address_kind=AddressKind.IP_NETMASK,
                value="192.0.2.10",
            )
        ],
    )
    result = DedupeAnalysisEngine().analyze(config)

    report_text = render_dedupe_analysis_markdown(result)
    report_path = export_dedupe_analysis_markdown(result, tmp_path / "dedupe.md")

    assert "# Frying-PAN Dedupe And Conflict Analysis" in report_text
    assert "Findings are advisory" in report_path.read_text(encoding="utf-8")
