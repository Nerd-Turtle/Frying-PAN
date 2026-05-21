from __future__ import annotations

from pathlib import Path

from frying_pan.normalized.config import NormalizedConfig
from frying_pan.normalized.vendor_metadata import (
    ConversionWarning,
    ConversionWarningSeverity,
)
from frying_pan.sources.base import SourceType
from frying_pan.workflows.convert.adapter_contract import ConversionAdapter
from frying_pan.workflows.convert.conversion_plan import (
    ConversionAction,
    ConversionDecision,
    ConversionPlan,
)
from frying_pan.workflows.convert.conversion_workflow import ConversionWorkflow
from frying_pan.workflows.convert.converted_import import ConvertedImportPackage
from frying_pan.workflows.convert.generic_json_adapter import (
    GenericJsonConversionAdapter,
    validate_conversion_package,
)

FIXTURES = Path(__file__).parent / "fixtures"


def test_conversion_plan_records_warning_decisions() -> None:
    decision = ConversionDecision(
        action=ConversionAction.ACCEPT_WARNING,
        source_ref="fortigate/policy/1",
        warnings=["Lossy conversion requires operator review."],
    )
    plan = ConversionPlan(source_config_id="vendor", decisions=[decision])

    assert plan.decisions[0].warnings


def test_generic_json_adapter_creates_converted_package() -> None:
    package = GenericJsonConversionAdapter().convert(
        FIXTURES / "vendor_future" / "generic_import.json"
    )

    assert package.source_format == "generic-json"
    assert package.scope_count == 1
    assert package.entity_count == 7
    assert package.security_rule_count == 1
    assert package.unsupported_count == 2
    assert package.validation.valid
    assert package.validation.warnings
    assert "dynamic_address_group" in {warning.code for warning in package.warnings}


def test_conversion_warning_serializes_review_fields() -> None:
    warning = ConversionWarning(
        code="lossy",
        message="Review required.",
        source_location="policy/1",
        source_field="schedule",
        normalized_target="security_rules[0].metadata",
        severity=ConversionWarningSeverity.HIGH,
        suggested_review="Confirm schedule handling before migration.",
    )

    dumped = warning.model_dump()

    assert dumped["severity"] == "high"
    assert dumped["source_field"] == "schedule"
    assert dumped["suggested_review"].startswith("Confirm")


def test_conversion_workflow_creates_review_plan_from_package() -> None:
    workflow = ConversionWorkflow()
    package = workflow.convert_generic_json(FIXTURES / "vendor_future" / "generic_import.json")
    plan = workflow.create_plan_from_package(package)

    assert plan.package_id == package.package_id
    assert plan.decision_count == 1
    assert plan.decisions[0].action == ConversionAction.REVIEW_PACKAGE
    assert plan.warnings


def test_invalid_converted_package_fails_validation() -> None:
    package = ConvertedImportPackage(
        name="invalid",
        normalized_config=NormalizedConfig(
            source_id="invalid",
            source_type=SourceType.NORMALIZED_IMPORT_FUTURE,
        ),
    )

    validation = validate_conversion_package(package)

    assert not validation.valid
    assert "at least one scope" in validation.errors[0]


def test_fake_adapter_implements_conversion_contract() -> None:
    class FakeAdapter(ConversionAdapter):
        source_format = "fake"

        def can_parse(self, path: Path) -> bool:
            return path.suffix == ".fake"

        def convert(self, path: Path) -> ConvertedImportPackage:
            return ConvertedImportPackage(
                name=path.stem,
                source_format=self.source_format,
                normalized_config=NormalizedConfig(
                    source_id=path.stem,
                    source_type=SourceType.NORMALIZED_IMPORT_FUTURE,
                ),
            )

    adapter = FakeAdapter()
    package = adapter.convert(Path("sample.fake"))

    assert adapter.can_parse(Path("sample.fake"))
    assert package.source_format == "fake"
