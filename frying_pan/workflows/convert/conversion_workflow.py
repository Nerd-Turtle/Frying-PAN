from __future__ import annotations

from pathlib import Path

from frying_pan.workflows.convert.conversion_plan import (
    ConversionAction,
    ConversionDecision,
    ConversionPlan,
)
from frying_pan.workflows.convert.converted_import import ConvertedImportPackage
from frying_pan.workflows.convert.generic_json_adapter import (
    GenericJsonConversionAdapter,
    validate_conversion_package,
)


class ConversionWorkflow:
    def create_plan(self, source_config_id: str) -> ConversionPlan:
        return ConversionPlan(source_config_id=source_config_id)

    def create_plan_from_package(self, package: ConvertedImportPackage) -> ConversionPlan:
        plan = ConversionPlan(
            source_config_id=package.normalized_config.source_id,
            package_id=package.package_id,
            warnings=[
                warning.message for warning in package.warnings
            ]
            + [feature.notes or feature.feature for feature in package.unsupported_features],
        )
        plan.decisions.append(
            ConversionDecision(
                action=ConversionAction.REVIEW_PACKAGE,
                source_ref=package.package_id,
                warnings=plan.warnings,
            )
        )
        return plan

    def stage_decision(self, plan: ConversionPlan, decision: ConversionDecision) -> ConversionPlan:
        plan.decisions.append(decision)
        return plan

    def convert_generic_json(self, path: Path) -> ConvertedImportPackage:
        return GenericJsonConversionAdapter().convert(path)

    def validate_package(self, package: ConvertedImportPackage):
        package.validation = validate_conversion_package(package)
        return package.validation
