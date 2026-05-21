from __future__ import annotations

from pathlib import Path

from frying_pan.export.conversion_report_exporter import export_conversion_report_markdown
from frying_pan.workflows.convert.conversion_workflow import ConversionWorkflow

FIXTURES = Path(__file__).parent / "fixtures"


def test_conversion_report_markdown_includes_warnings_and_limitations(
    tmp_path: Path,
) -> None:
    workflow = ConversionWorkflow()
    package = workflow.convert_generic_json(FIXTURES / "vendor_future" / "generic_import.json")
    plan = workflow.create_plan_from_package(package)
    report_path = tmp_path / "conversion.md"

    export_conversion_report_markdown(package, plan, report_path)

    report = report_path.read_text(encoding="utf-8")
    assert "Frying-PAN Conversion Report" in report
    assert "dynamic_address_group" in report
    assert "XML mutation/export remains blocked" in report
