from __future__ import annotations

from frying_pan.normalized.config import NormalizedConfig
from frying_pan.normalized.entity import NormalizedEntity
from frying_pan.normalized.rules import RulebaseType, SecurityRule
from frying_pan.policy.assurance.assurance_engine import PolicyAssuranceEngine
from frying_pan.policy.assurance.behavior_diff import BehaviorDiff
from frying_pan.policy.assurance.behavior_snapshot import BehaviorSnapshot
from frying_pan.policy.match.match_engine import PolicyMatchEngine
from frying_pan.policy.match.test_case import PolicyTestCase
from frying_pan.workflows.migrate.migration_plan import (
    MigrationAction,
    MigrationPlan,
    MigrationPlanPreview,
    MigrationPlanStatus,
    MigrationValidation,
    MigrationValidationLevel,
    MigrationValidationMessage,
    PlanDecision,
)
from frying_pan.workflows.migrate.object_mapping import ObjectMapping, ObjectMappingMode
from frying_pan.workflows.migrate.rule_mapping import RuleMapping, RulePlacementMode
from frying_pan.workflows.migrate.scope_mapping import ScopeMapping, ZoneMapping


class MigrationWorkflow:
    def create_plan(self, source_config_ids: list[str], target_config_id: str) -> MigrationPlan:
        return MigrationPlan(
            source_config_ids=source_config_ids,
            target_config_id=target_config_id,
            warnings=[
                "Migration plans are staged decisions only; source and target XML are not mutated."
            ],
        )

    def create_plan_from_configs(
        self, source_config: NormalizedConfig, target_config: NormalizedConfig
    ) -> MigrationPlan:
        return MigrationPlan(
            source_config_ids=[source_config.source_id],
            target_config_id=target_config.source_id,
            source_type=source_config.source_type.value,
            target_type=target_config.source_type.value,
            warnings=[
                "Migration plans are staged decisions only; source and target XML are not mutated."
            ],
        )

    def stage_decision(self, plan: MigrationPlan, decision: PlanDecision) -> MigrationPlan:
        plan.decisions.append(decision)
        return plan

    def stage_scope_mapping(
        self, plan: MigrationPlan, source_scope_path: str, target_scope_path: str
    ) -> MigrationPlan:
        mapping = ScopeMapping(
            source_scope_path=source_scope_path,
            target_scope_path=target_scope_path,
            warnings=["Review Panorama hierarchy and local firewall context before export."],
        )
        plan.scope_mappings.append(mapping)
        return self.stage_decision(
            plan,
            PlanDecision(
                action=MigrationAction.MAP_SCOPE,
                source_ref=source_scope_path,
                target_ref=target_scope_path,
                warnings=mapping.warnings,
            ),
        )

    def stage_zone_mapping(
        self, plan: MigrationPlan, source_zone: str, target_zone: str
    ) -> MigrationPlan:
        mapping = ZoneMapping(source_zone=source_zone, target_zone=target_zone)
        plan.zone_mappings.append(mapping)
        return self.stage_decision(
            plan,
            PlanDecision(
                action=MigrationAction.MAP_ZONE,
                source_ref=source_zone,
                target_ref=target_zone,
            ),
        )

    def stage_object_mapping(
        self,
        plan: MigrationPlan,
        source_object_ref: str,
        *,
        target_object_ref: str | None = None,
        mode: ObjectMappingMode = ObjectMappingMode.COPY,
    ) -> MigrationPlan:
        mapping = ObjectMapping(
            source_object_ref=source_object_ref,
            target_object_ref=target_object_ref,
            mode=mode,
        )
        plan.object_mappings.append(mapping)
        return self.stage_decision(
            plan,
            PlanDecision(
                action=MigrationAction.MAP_OBJECT,
                source_ref=source_object_ref,
                target_ref=target_object_ref,
                parameters={"mode": mode.value},
            ),
        )

    def stage_rule_placement(
        self,
        plan: MigrationPlan,
        source_rule_ref: str,
        target_rulebase_ref: str,
        *,
        placement_mode: RulePlacementMode = RulePlacementMode.APPEND,
        anchor_ref: str | None = None,
    ) -> MigrationPlan:
        mapping = RuleMapping(
            source_rule_ref=source_rule_ref,
            target_rulebase_ref=target_rulebase_ref,
            placement_mode=placement_mode,
            insert_after_rule_ref=anchor_ref
            if placement_mode == RulePlacementMode.INSERT_AFTER
            else None,
            insert_before_rule_ref=anchor_ref
            if placement_mode == RulePlacementMode.INSERT_BEFORE
            else None,
        )
        plan.rule_mappings.append(mapping)
        return self.stage_decision(
            plan,
            PlanDecision(
                action=MigrationAction.PLACE_RULE,
                source_ref=source_rule_ref,
                target_ref=target_rulebase_ref,
                parameters={"placement_mode": placement_mode.value, "anchor_ref": anchor_ref},
                warnings=["Rule placement is staged only; target XML is not mutated."],
            ),
        )

    def include_dependencies(
        self, source_config: NormalizedConfig, plan: MigrationPlan, source_owner_name: str
    ) -> MigrationPlan:
        for dependency in source_config.dependencies:
            if dependency.owner_name != source_owner_name:
                continue
            ref = f"{dependency.owner_scope_path}/{dependency.owner_name}->{dependency.target_name}"
            if ref in plan.dependency_refs:
                continue
            plan.dependency_refs.append(ref)
            self.stage_decision(
                plan,
                PlanDecision(
                    action=MigrationAction.INCLUDE_DEPENDENCY,
                    source_ref=ref,
                    warnings=dependency.warnings,
                ),
            )
        return plan

    def compare_test_flow(
        self,
        source_config: NormalizedConfig,
        target_config: NormalizedConfig,
        plan: MigrationPlan,
        test_case: PolicyTestCase,
        *,
        source_scope_path: str | None = None,
        target_scope_path: str | None = None,
    ) -> BehaviorDiff:
        matcher = PolicyMatchEngine()
        before = matcher.evaluate_config(source_config, test_case, source_scope_path)
        after = matcher.evaluate_config(target_config, test_case, target_scope_path)
        diff = PolicyAssuranceEngine().compare(
            BehaviorSnapshot(
                test_case=test_case,
                matched_rule_name=before.matched_rule.name if before.matched_rule else None,
                action=before.action,
            ),
            BehaviorSnapshot(
                test_case=test_case,
                matched_rule_name=after.matched_rule.name if after.matched_rule else None,
                action=after.action,
            ),
        )
        diff.warnings.append(
            "Phase 6 assurance compares imported source/target configs; staged decisions are "
            "not serialized into a target config for full simulation."
        )
        plan.assurance_results.append(diff)
        return diff

    def validate_plan(
        self,
        source_config: NormalizedConfig,
        target_config: NormalizedConfig,
        plan: MigrationPlan,
    ) -> MigrationValidation:
        messages: list[MigrationValidationMessage] = []
        for mapping in plan.scope_mappings:
            if not _scope_exists(source_config, mapping.source_scope_path):
                messages.append(
                    MigrationValidationMessage(
                        level=MigrationValidationLevel.ERROR,
                        message=f"Source scope {mapping.source_scope_path!r} was not found.",
                    )
                )
            if not _scope_exists(target_config, mapping.target_scope_path):
                messages.append(
                    MigrationValidationMessage(
                        level=MigrationValidationLevel.ERROR,
                        message=f"Target scope {mapping.target_scope_path!r} was not found.",
                    )
                )
        for mapping in plan.object_mappings:
            source = _find_entity_by_ref(source_config, mapping.source_object_ref)
            if source is None:
                messages.append(
                    MigrationValidationMessage(
                        level=MigrationValidationLevel.ERROR,
                        message=f"Source object {mapping.source_object_ref!r} was not found.",
                    )
                )
            if mapping.target_object_ref and _find_entity_by_ref(
                target_config, mapping.target_object_ref
            ) is None and mapping.mode in {ObjectMappingMode.REUSE_TARGET, ObjectMappingMode.MERGE}:
                messages.append(
                    MigrationValidationMessage(
                        level=MigrationValidationLevel.ERROR,
                        message=f"Target object {mapping.target_object_ref!r} was not found.",
                    )
                )
        for mapping in plan.rule_mappings:
            if _find_rule_by_ref(source_config, mapping.source_rule_ref) is None:
                messages.append(
                    MigrationValidationMessage(
                        level=MigrationValidationLevel.ERROR,
                        message=f"Source rule {mapping.source_rule_ref!r} was not found.",
                    )
                )
            target_scope = mapping.target_rulebase_ref.split("::", maxsplit=1)[0]
            if not _scope_exists(target_config, target_scope):
                messages.append(
                    MigrationValidationMessage(
                        level=MigrationValidationLevel.ERROR,
                        message=f"Target rulebase scope {target_scope!r} was not found.",
                    )
                )
        if any(dependency.resolved is False for dependency in source_config.dependencies):
            messages.append(
                MigrationValidationMessage(
                    level=MigrationValidationLevel.WARNING,
                    message=(
                        "Source configuration has unresolved dependencies; migration plan "
                        "dependency inclusion may be incomplete."
                    ),
                )
            )
        if plan.assurance_required and not plan.assurance_results:
            messages.append(
                MigrationValidationMessage(
                    level=MigrationValidationLevel.WARNING,
                    message=(
                        "Policy assurance is required but no assurance comparisons are attached."
                    ),
                )
            )
        validation = MigrationValidation(messages=messages)
        plan.validation = validation
        plan.status = (
            MigrationPlanStatus.BLOCKED
            if validation.has_errors
            else MigrationPlanStatus.READY_FOR_REVIEW
            if plan.decisions
            else MigrationPlanStatus.DRAFT
        )
        return validation

    def preview_plan(self, plan: MigrationPlan) -> MigrationPlanPreview:
        return MigrationPlanPreview(
            source_config_ids=plan.source_config_ids,
            target_config_id=plan.target_config_id,
            decision_summaries=[
                f"{decision.action.value}: {decision.source_ref}"
                + (f" -> {decision.target_ref}" if decision.target_ref else "")
                for decision in plan.decisions
            ],
            dependency_summaries=plan.dependency_refs,
            assurance_summaries=[
                "changed" if result.behavior_changed else "unchanged"
                for result in plan.assurance_results
            ],
            warnings=[
                *plan.warnings,
                "Phase 6 preview is not XML output; serializer validation is still required.",
            ],
        )


def _scope_exists(config: NormalizedConfig, scope_path: str) -> bool:
    return any(scope.path == scope_path for scope in config.scopes)


def _find_entity_by_ref(config: NormalizedConfig, ref: str) -> NormalizedEntity | None:
    try:
        scope_path, entity_type, name = ref.split("::", maxsplit=2)
    except ValueError:
        return None
    return next(
        (
            entity
            for entity in config.entities
            if entity.scope_path == scope_path
            and entity.entity_type.value == entity_type
            and entity.name == name
        ),
        None,
    )


def _find_rule_by_ref(config: NormalizedConfig, ref: str) -> SecurityRule | None:
    try:
        scope_path, rulebase_type, name = ref.split("::", maxsplit=2)
    except ValueError:
        return None
    try:
        parsed_rulebase_type = RulebaseType(rulebase_type)
    except ValueError:
        return None
    return next(
        (
            rule
            for rule in config.security_rules
            if rule.scope_path == scope_path
            and rule.rulebase_type == parsed_rulebase_type
            and rule.name == name
        ),
        None,
    )
