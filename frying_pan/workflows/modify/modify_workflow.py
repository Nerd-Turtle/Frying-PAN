from __future__ import annotations

from frying_pan.normalized.config import NormalizedConfig
from frying_pan.normalized.entity import NormalizedEntity
from frying_pan.normalized.references import Reference
from frying_pan.normalized.rules import RulebaseType, SecurityRule
from frying_pan.workflows.modify.actions import ModifyPlanPreview, summarize_decision
from frying_pan.workflows.modify.modify_plan import (
    ModificationPlan,
    ModifyAction,
    ModifyPlanDecision,
    ModifyPlanStatus,
    ModifyPlanValidation,
    ModifyValidationMessage,
    ValidationLevel,
)


class ModifyWorkflow:
    def create_plan(
        self, source_config_id: str, source_type: str | None = None
    ) -> ModificationPlan:
        return ModificationPlan(
            source_config_id=source_config_id,
            source_type=source_type,
            warnings=[
                "Modify plans are staged decisions only; source XML is not mutated in Phase 5."
            ],
        )

    def create_plan_from_config(self, config: NormalizedConfig) -> ModificationPlan:
        return self.create_plan(config.source_id, config.source_type.value)

    def stage_decision(
        self, plan: ModificationPlan, decision: ModifyPlanDecision
    ) -> ModificationPlan:
        plan.decisions.append(decision)
        return plan

    def stage_object_rename(
        self,
        config: NormalizedConfig,
        plan: ModificationPlan,
        *,
        scope_path: str,
        entity_type: str,
        object_name: str,
        new_name: str,
    ) -> ModificationPlan:
        source_ref = _entity_ref(scope_path, entity_type, object_name)
        target_ref = _entity_ref(scope_path, entity_type, new_name)
        warnings: list[str] = []
        if _find_entity(config, scope_path, entity_type, new_name) is not None:
            warnings.append(f"Target object {target_ref} already exists.")
        decision = ModifyPlanDecision(
            action=ModifyAction.RENAME_OBJECT,
            source_ref=source_ref,
            target_ref=target_ref,
            impacted_references=_impacted_references(config.references, object_name),
            warnings=warnings,
            parameters={"new_name": new_name},
        )
        return self.stage_decision(plan, decision)

    def stage_object_dedupe(
        self,
        config: NormalizedConfig,
        plan: ModificationPlan,
        *,
        duplicate_scope_path: str,
        entity_type: str,
        duplicate_name: str,
        canonical_scope_path: str,
        canonical_name: str,
    ) -> ModificationPlan:
        source_ref = _entity_ref(duplicate_scope_path, entity_type, duplicate_name)
        target_ref = _entity_ref(canonical_scope_path, entity_type, canonical_name)
        decision = ModifyPlanDecision(
            action=ModifyAction.DEDUPE_OBJECT,
            source_ref=source_ref,
            target_ref=target_ref,
            impacted_references=_impacted_references(config.references, duplicate_name),
            warnings=[
                "Dedupe action is staged only; review impacted references before approval."
            ],
            parameters={"canonical_name": canonical_name},
        )
        return self.stage_decision(plan, decision)

    def stage_object_move(
        self,
        config: NormalizedConfig,
        plan: ModificationPlan,
        *,
        source_scope_path: str,
        target_scope_path: str,
        entity_type: str,
        object_name: str,
    ) -> ModificationPlan:
        source_ref = _entity_ref(source_scope_path, entity_type, object_name)
        target_ref = _entity_ref(target_scope_path, entity_type, object_name)
        warnings = [
            "Object move requires Panorama inheritance/override review before export."
        ]
        if not any(scope.path == target_scope_path for scope in config.scopes):
            warnings.append(f"Target scope {target_scope_path!r} was not found.")
        if _find_entity(config, target_scope_path, entity_type, object_name) is not None:
            warnings.append(f"Target object {target_ref} already exists.")
        decision = ModifyPlanDecision(
            action=ModifyAction.MOVE_OBJECT,
            source_ref=source_ref,
            target_ref=target_ref,
            impacted_references=_impacted_references(config.references, object_name),
            warnings=warnings,
            parameters={"target_scope_path": target_scope_path},
        )
        return self.stage_decision(plan, decision)

    def stage_rule_reorder(
        self,
        config: NormalizedConfig,
        plan: ModificationPlan,
        *,
        scope_path: str,
        rulebase_type: RulebaseType,
        rule_name: str,
        new_position: int,
    ) -> ModificationPlan:
        rule = _find_rule(config, scope_path, rulebase_type, rule_name)
        source_ref = _rule_ref(scope_path, rulebase_type, rule_name)
        warnings = []
        if rule is None:
            warnings.append(f"Rule {source_ref} was not found.")
        decision = ModifyPlanDecision(
            action=ModifyAction.REORDER_RULE,
            source_ref=source_ref,
            parameters={
                "old_position": rule.position if rule else None,
                "new_position": new_position,
                "scope_path": scope_path,
                "rulebase_type": rulebase_type.value,
            },
            warnings=warnings,
        )
        return self.stage_decision(plan, decision)

    def stage_rule_metadata(
        self,
        config: NormalizedConfig,
        plan: ModificationPlan,
        *,
        scope_path: str,
        rulebase_type: RulebaseType,
        rule_name: str,
        field: str,
        value: bool | str,
    ) -> ModificationPlan:
        rule = _find_rule(config, scope_path, rulebase_type, rule_name)
        action = (
            ModifyAction.SET_RULE_ENABLED
            if field == "enabled"
            else ModifyAction.SET_RULE_LOGGING
        )
        source_ref = _rule_ref(scope_path, rulebase_type, rule_name)
        warnings = []
        if rule is None:
            warnings.append(f"Rule {source_ref} was not found.")
        decision = ModifyPlanDecision(
            action=action,
            source_ref=source_ref,
            parameters={"field": field, "value": value},
            warnings=warnings,
        )
        return self.stage_decision(plan, decision)

    def validate_plan(
        self, config: NormalizedConfig, plan: ModificationPlan
    ) -> ModifyPlanValidation:
        messages: list[ModifyValidationMessage] = []
        seen_sources: set[str] = set()
        for decision in plan.decisions:
            if decision.source_ref in seen_sources:
                messages.append(
                    ModifyValidationMessage(
                        level=ValidationLevel.ERROR,
                        action_id=decision.id,
                        message=f"Multiple actions target {decision.source_ref}.",
                    )
                )
            seen_sources.add(decision.source_ref)
            messages.extend(_decision_messages(config, decision))
            for warning in decision.warnings:
                messages.append(
                    ModifyValidationMessage(
                        level=ValidationLevel.WARNING,
                        action_id=decision.id,
                        message=warning,
                    )
                )
        if any(reference.resolved is False for reference in config.references):
            messages.append(
                ModifyValidationMessage(
                    level=ValidationLevel.WARNING,
                    message=(
                        "Imported configuration has unresolved references; staged impact "
                        "may be incomplete."
                    ),
                )
            )
        validation = ModifyPlanValidation(messages=messages)
        plan.validation = validation
        plan.status = (
            ModifyPlanStatus.BLOCKED
            if validation.has_errors
            else ModifyPlanStatus.READY_FOR_REVIEW
            if plan.decisions
            else ModifyPlanStatus.DRAFT
        )
        return validation

    def preview_plan(self, plan: ModificationPlan) -> ModifyPlanPreview:
        return ModifyPlanPreview(
            source_config_id=plan.source_config_id,
            action_summaries=[summarize_decision(decision) for decision in plan.decisions],
            impacted_reference_summaries=[
                f"{decision.source_ref}: {len(decision.impacted_references)} impacted references"
                for decision in plan.decisions
            ],
            warnings=[
                *plan.warnings,
                "Phase 5 preview is not XML output; serializer validation is still required.",
            ],
        )


def _decision_messages(
    config: NormalizedConfig, decision: ModifyPlanDecision
) -> list[ModifyValidationMessage]:
    messages: list[ModifyValidationMessage] = []
    if decision.action in {
        ModifyAction.RENAME_OBJECT,
        ModifyAction.MOVE_OBJECT,
        ModifyAction.DEDUPE_OBJECT,
    }:
        scope_path, entity_type, name = _parse_entity_ref(decision.source_ref)
        if _find_entity(config, scope_path, entity_type, name) is None:
            messages.append(
                ModifyValidationMessage(
                    level=ValidationLevel.ERROR,
                    action_id=decision.id,
                    message=f"Source object {decision.source_ref} was not found.",
                )
            )
    return messages


def _find_entity(
    config: NormalizedConfig, scope_path: str, entity_type: str, name: str
) -> NormalizedEntity | None:
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


def _find_rule(
    config: NormalizedConfig, scope_path: str, rulebase_type: RulebaseType, rule_name: str
) -> SecurityRule | None:
    return next(
        (
            rule
            for rule in config.security_rules
            if rule.scope_path == scope_path
            and rule.rulebase_type == rulebase_type
            and rule.name == rule_name
        ),
        None,
    )


def _impacted_references(references: list[Reference], target_name: str) -> list[str]:
    return [
        f"{reference.owner_scope_path}/{reference.owner_name}:{reference.reference_kind.value}"
        for reference in references
        if reference.target_name == target_name
    ]


def _entity_ref(scope_path: str, entity_type: str, name: str) -> str:
    return f"{scope_path}::{entity_type}::{name}"


def _rule_ref(scope_path: str, rulebase_type: RulebaseType, name: str) -> str:
    return f"{scope_path}::{rulebase_type.value}::{name}"


def _parse_entity_ref(ref: str) -> tuple[str, str, str]:
    scope_path, entity_type, name = ref.split("::", maxsplit=2)
    return scope_path, entity_type, name
