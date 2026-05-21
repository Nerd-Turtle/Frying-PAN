from __future__ import annotations

from pathlib import Path

from frying_pan.analysis.inventory import summarize_inventory
from frying_pan.export.report_exporter import export_inventory_markdown, render_inventory_markdown
from frying_pan.sources.base import SourceConfig, SourceType
from frying_pan.sources.panorama_xml import PanoramaXmlAdapter

FIXTURES = Path(__file__).parent / "fixtures"


def test_inventory_markdown_report_from_parsed_fixture(tmp_path: Path) -> None:
    source_path = FIXTURES / "panorama" / "reference_config_items.xml"
    source = SourceConfig(
        display_name=source_path.name,
        original_path=source_path,
        source_type=SourceType.PANORAMA_XML,
    )
    config = PanoramaXmlAdapter().parse(source)
    report_path = export_inventory_markdown(config, tmp_path / "report.md")
    report_text = report_path.read_text(encoding="utf-8")

    assert "# Frying-PAN Inventory Report" in report_text
    assert "Source type: `panorama_xml`" in report_text
    assert "Unresolved references:" in report_text
    assert "XML mutation/export remains blocked" in report_text
    assert "does not imply XML mutation, migration" in report_text


def test_render_inventory_markdown_labels_limitations() -> None:
    source_path = FIXTURES / "panorama" / "reference_config_items.xml"
    source = SourceConfig(
        display_name=source_path.name,
        original_path=source_path,
        source_type=SourceType.PANORAMA_XML,
    )
    config = PanoramaXmlAdapter().parse(source)

    assert "Warnings And Limitations" in render_inventory_markdown(summarize_inventory(config))
