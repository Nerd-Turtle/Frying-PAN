from __future__ import annotations

import argparse
import sys
from pathlib import Path

from frying_pan.analysis.dedupe import DedupeAnalysisEngine
from frying_pan.analysis.inventory import summarize_inventory
from frying_pan.export.conversion_report_exporter import export_conversion_report_markdown
from frying_pan.export.dedupe_report_exporter import export_dedupe_analysis_markdown
from frying_pan.export.migration_plan_exporter import export_migration_plan_markdown
from frying_pan.export.modify_plan_exporter import export_modify_plan_markdown
from frying_pan.export.policy_audit_exporter import export_policy_audit_markdown
from frying_pan.export.policy_test_exporter import export_policy_test_markdown
from frying_pan.export.report_exporter import export_inventory_markdown
from frying_pan.normalized.rules import RulebaseType
from frying_pan.policy.audit.audit_engine import PolicyAuditEngine
from frying_pan.policy.match.match_engine import PolicyMatchEngine
from frying_pan.policy.match.test_case import PolicyTestCase
from frying_pan.sources.detection import detect_source
from frying_pan.sources.parsing import SourceParseError, parse_source
from frying_pan.storage.workspace import ProjectWorkspace
from frying_pan.workflows.convert.conversion_workflow import ConversionWorkflow
from frying_pan.workflows.migrate.migration_workflow import MigrationWorkflow
from frying_pan.workflows.migrate.object_mapping import ObjectMappingMode
from frying_pan.workflows.migrate.rule_mapping import RulePlacementMode
from frying_pan.workflows.modify.modify_workflow import ModifyWorkflow


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="frying-pan")
    subparsers = parser.add_subparsers(dest="command", required=True)

    detect_parser = subparsers.add_parser("detect", help="Detect a source configuration type.")
    detect_parser.add_argument("source", type=Path)

    inventory_parser = subparsers.add_parser("inventory", help="Parse and summarize inventory.")
    inventory_parser.add_argument("source", type=Path)
    inventory_parser.add_argument(
        "--json", action="store_true", help="Print JSON inventory summary."
    )
    inventory_parser.add_argument(
        "--report-md", type=Path, help="Write a Markdown inventory report."
    )

    workspace_parser = subparsers.add_parser(
        "workspace-create", help="Create a portable Frying-PAN project workspace."
    )
    workspace_parser.add_argument("path", type=Path)
    workspace_parser.add_argument("--name", default="Frying-PAN Project")

    import_parser = subparsers.add_parser("import-source", help="Import a source into a workspace.")
    import_parser.add_argument("workspace", type=Path)
    import_parser.add_argument("source", type=Path)

    policy_test_parser = subparsers.add_parser(
        "policy-test", help="Evaluate one test flow against imported security policy."
    )
    policy_test_parser.add_argument("source", type=Path)
    policy_test_parser.add_argument("--scope", help="Scope path, such as vsys/vsys1.")
    policy_test_parser.add_argument("--src-zone", required=True)
    policy_test_parser.add_argument("--dst-zone", required=True)
    policy_test_parser.add_argument("--src-ip", required=True)
    policy_test_parser.add_argument("--dst-ip", required=True)
    policy_test_parser.add_argument("--protocol", required=True)
    policy_test_parser.add_argument("--dst-port", type=int)
    policy_test_parser.add_argument("--src-port", type=int)
    policy_test_parser.add_argument("--application", default="any")
    policy_test_parser.add_argument("--user", default="any")
    policy_test_parser.add_argument("--url-category")
    policy_test_parser.add_argument(
        "--json", action="store_true", help="Print JSON policy test result."
    )
    policy_test_parser.add_argument(
        "--report-md", type=Path, help="Write a Markdown result report."
    )

    policy_audit_parser = subparsers.add_parser(
        "policy-audit", help="Audit imported security policy for review findings."
    )
    policy_audit_parser.add_argument("source", type=Path)
    policy_audit_parser.add_argument("--scope", help="Scope path, such as vsys/vsys1.")
    policy_audit_parser.add_argument(
        "--json", action="store_true", help="Print JSON policy audit result."
    )
    policy_audit_parser.add_argument(
        "--report-md", type=Path, help="Write a Markdown audit report."
    )

    dedupe_parser = subparsers.add_parser(
        "dedupe-analysis", help="Analyze object duplicates, conflicts, and unused candidates."
    )
    dedupe_parser.add_argument("source", type=Path)
    dedupe_parser.add_argument(
        "--json", action="store_true", help="Print JSON dedupe/conflict analysis result."
    )
    dedupe_parser.add_argument(
        "--report-md", type=Path, help="Write a Markdown dedupe/conflict report."
    )

    modify_parser = subparsers.add_parser(
        "modify-plan", help="Stage and validate a local single-config Modify plan."
    )
    modify_parser.add_argument("source", type=Path)
    modify_parser.add_argument(
        "--rename-object",
        nargs=4,
        action="append",
        metavar=("SCOPE", "TYPE", "OLD_NAME", "NEW_NAME"),
        help="Stage object rename.",
    )
    modify_parser.add_argument(
        "--move-object",
        nargs=4,
        action="append",
        metavar=("SOURCE_SCOPE", "TARGET_SCOPE", "TYPE", "NAME"),
        help="Stage object move.",
    )
    modify_parser.add_argument(
        "--dedupe-object",
        nargs=5,
        action="append",
        metavar=("DUP_SCOPE", "TYPE", "DUP_NAME", "CANON_SCOPE", "CANON_NAME"),
        help="Stage duplicate object replacement.",
    )
    modify_parser.add_argument(
        "--reorder-rule",
        nargs=4,
        action="append",
        metavar=("SCOPE", "RULEBASE_TYPE", "RULE_NAME", "NEW_POSITION"),
        help="Stage rule reorder inside the same scope/rulebase.",
    )
    modify_parser.add_argument(
        "--json", action="store_true", help="Print JSON Modify plan."
    )
    modify_parser.add_argument("--report-md", type=Path, help="Write a Markdown plan report.")

    migrate_parser = subparsers.add_parser(
        "migrate-plan", help="Stage and validate a source-to-target migration plan."
    )
    migrate_parser.add_argument("source", type=Path)
    migrate_parser.add_argument("target", type=Path)
    migrate_parser.add_argument(
        "--map-scope",
        nargs=2,
        action="append",
        metavar=("SOURCE_SCOPE", "TARGET_SCOPE"),
        help="Stage source-to-target scope mapping.",
    )
    migrate_parser.add_argument(
        "--map-zone",
        nargs=2,
        action="append",
        metavar=("SOURCE_ZONE", "TARGET_ZONE"),
        help="Stage source-to-target zone mapping.",
    )
    migrate_parser.add_argument(
        "--map-object",
        nargs=3,
        action="append",
        metavar=("SOURCE_REF", "TARGET_REF", "MODE"),
        help="Stage object mapping using copy, reuse_target, rename_and_copy, merge, or skip.",
    )
    migrate_parser.add_argument(
        "--place-rule",
        nargs=3,
        action="append",
        metavar=("SOURCE_RULE_REF", "TARGET_RULEBASE_REF", "MODE"),
        help="Stage rule placement using append, insert_after, or insert_before.",
    )
    migrate_parser.add_argument(
        "--include-dependencies",
        action="append",
        metavar="OWNER_NAME",
        help="Include parsed dependencies for a source owner name.",
    )
    migrate_parser.add_argument(
        "--json", action="store_true", help="Print JSON Migration plan."
    )
    migrate_parser.add_argument(
        "--report-md", type=Path, help="Write a Markdown migration plan report."
    )

    convert_parser = subparsers.add_parser(
        "convert", help="Convert a generic local source into a normalized import package."
    )
    convert_parser.add_argument("source", type=Path)
    convert_parser.add_argument(
        "--format",
        choices=["generic-json"],
        default="generic-json",
        help="Input conversion format.",
    )
    convert_parser.add_argument(
        "--json", action="store_true", help="Print JSON converted import package."
    )
    convert_parser.add_argument(
        "--report-md", type=Path, help="Write a Markdown conversion report."
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "detect":
        result = detect_source(args.source)
        print(result.model_dump_json(indent=2))
        return 0

    if args.command == "inventory":
        try:
            config = parse_source(args.source)
        except SourceParseError as exc:
            print(exc, file=sys.stderr)
            return 1
        summary = summarize_inventory(config)
        if args.report_md:
            export_inventory_markdown(summary, args.report_md)
        if args.json:
            print(summary.model_dump_json(indent=2))
        else:
            print(_format_inventory_summary(summary))
            if args.report_md:
                print(f"Markdown report written to {args.report_md}")
        return 0

    if args.command == "workspace-create":
        workspace = ProjectWorkspace.create(args.path, args.name)
        print(workspace.manifest.model_dump_json(indent=2))
        return 0

    if args.command == "import-source":
        workspace = ProjectWorkspace.open(args.workspace)
        source = workspace.import_source(args.source)
        print(source.model_dump_json(indent=2))
        return 0

    if args.command == "policy-test":
        try:
            config = parse_source(args.source)
            test_case = PolicyTestCase(
                source_zone=args.src_zone,
                destination_zone=args.dst_zone,
                source_ip=args.src_ip,
                destination_ip=args.dst_ip,
                protocol=args.protocol,
                destination_port=args.dst_port,
                source_port=args.src_port,
                application=args.application,
                user=args.user,
                url_category=args.url_category,
            )
        except (SourceParseError, ValueError) as exc:
            print(exc, file=sys.stderr)
            return 1
        result = PolicyMatchEngine().evaluate_config(config, test_case, args.scope)
        if args.report_md:
            export_policy_test_markdown(test_case, result, args.report_md)
        if args.json:
            print(result.model_dump_json(indent=2))
        else:
            print(_format_policy_test_result(result))
            if args.report_md:
                print(f"Markdown report written to {args.report_md}")
        return 0

    if args.command == "policy-audit":
        try:
            config = parse_source(args.source)
        except SourceParseError as exc:
            print(exc, file=sys.stderr)
            return 1
        result = PolicyAuditEngine().audit_config(config, args.scope)
        if args.report_md:
            export_policy_audit_markdown(result, args.report_md)
        if args.json:
            print(result.model_dump_json(indent=2))
        else:
            print(_format_policy_audit_result(result))
            if args.report_md:
                print(f"Markdown report written to {args.report_md}")
        return 0

    if args.command == "dedupe-analysis":
        try:
            config = parse_source(args.source)
        except SourceParseError as exc:
            print(exc, file=sys.stderr)
            return 1
        result = DedupeAnalysisEngine().analyze(config)
        if args.report_md:
            export_dedupe_analysis_markdown(result, args.report_md)
        if args.json:
            print(result.model_dump_json(indent=2))
        else:
            print(_format_dedupe_analysis_result(result))
            if args.report_md:
                print(f"Markdown report written to {args.report_md}")
        return 0

    if args.command == "modify-plan":
        try:
            config = parse_source(args.source)
            workflow = ModifyWorkflow()
            plan = workflow.create_plan_from_config(config)
            for scope, entity_type, old_name, new_name in args.rename_object or []:
                workflow.stage_object_rename(
                    config,
                    plan,
                    scope_path=scope,
                    entity_type=entity_type,
                    object_name=old_name,
                    new_name=new_name,
                )
            for source_scope, target_scope, entity_type, name in args.move_object or []:
                workflow.stage_object_move(
                    config,
                    plan,
                    source_scope_path=source_scope,
                    target_scope_path=target_scope,
                    entity_type=entity_type,
                    object_name=name,
                )
            for dup_scope, entity_type, dup_name, canon_scope, canon_name in (
                args.dedupe_object or []
            ):
                workflow.stage_object_dedupe(
                    config,
                    plan,
                    duplicate_scope_path=dup_scope,
                    entity_type=entity_type,
                    duplicate_name=dup_name,
                    canonical_scope_path=canon_scope,
                    canonical_name=canon_name,
                )
            for scope, rulebase_type, rule_name, new_position in args.reorder_rule or []:
                workflow.stage_rule_reorder(
                    config,
                    plan,
                    scope_path=scope,
                    rulebase_type=RulebaseType(rulebase_type),
                    rule_name=rule_name,
                    new_position=int(new_position),
                )
            workflow.validate_plan(config, plan)
            preview = workflow.preview_plan(plan)
        except (SourceParseError, ValueError) as exc:
            print(exc, file=sys.stderr)
            return 1
        if args.report_md:
            export_modify_plan_markdown(plan, preview, args.report_md)
        if args.json:
            print(plan.model_dump_json(indent=2))
        else:
            print(_format_modify_plan(plan))
            if args.report_md:
                print(f"Markdown report written to {args.report_md}")
        return 0

    if args.command == "migrate-plan":
        try:
            source_config = parse_source(args.source)
            target_config = parse_source(args.target)
            workflow = MigrationWorkflow()
            plan = workflow.create_plan_from_configs(source_config, target_config)
            for source_scope, target_scope in args.map_scope or []:
                workflow.stage_scope_mapping(plan, source_scope, target_scope)
            for source_zone, target_zone in args.map_zone or []:
                workflow.stage_zone_mapping(plan, source_zone, target_zone)
            for source_ref, target_ref, mode in args.map_object or []:
                workflow.stage_object_mapping(
                    plan,
                    source_ref,
                    target_object_ref=target_ref if target_ref != "-" else None,
                    mode=ObjectMappingMode(mode),
                )
            for source_rule_ref, target_rulebase_ref, mode in args.place_rule or []:
                workflow.stage_rule_placement(
                    plan,
                    source_rule_ref,
                    target_rulebase_ref,
                    placement_mode=RulePlacementMode(mode),
                )
            for owner_name in args.include_dependencies or []:
                workflow.include_dependencies(source_config, plan, owner_name)
            workflow.validate_plan(source_config, target_config, plan)
            preview = workflow.preview_plan(plan)
        except (SourceParseError, ValueError) as exc:
            print(exc, file=sys.stderr)
            return 1
        if args.report_md:
            export_migration_plan_markdown(plan, preview, args.report_md)
        if args.json:
            print(plan.model_dump_json(indent=2))
        else:
            print(_format_migration_plan(plan))
            if args.report_md:
                print(f"Markdown report written to {args.report_md}")
        return 0

    if args.command == "convert":
        try:
            workflow = ConversionWorkflow()
            if args.format != "generic-json":
                raise ValueError(f"Unsupported conversion format {args.format!r}.")
            package = workflow.convert_generic_json(args.source)
            validation = workflow.validate_package(package)
            if validation.errors:
                raise ValueError("; ".join(validation.errors))
            plan = workflow.create_plan_from_package(package)
        except (OSError, ValueError) as exc:
            print(exc, file=sys.stderr)
            return 1
        if args.report_md:
            export_conversion_report_markdown(package, plan, args.report_md)
        if args.json:
            print(package.model_dump_json(indent=2))
        else:
            print(_format_conversion_package(package, plan))
            if args.report_md:
                print(f"Markdown report written to {args.report_md}")
        return 0

    parser.error("unknown command")
    return 2


def _format_inventory_summary(summary) -> str:
    return "\n".join(
        [
            "Frying-PAN Inventory Summary",
            f"Source type: {summary.source_type}",
            f"Scopes: {summary.scope_count}",
            f"Entities: {summary.entity_count}",
            f"Security rules: {summary.security_rule_count}",
            f"References: {summary.reference_count}",
            f"Unresolved references: {summary.unresolved_reference_count}",
            f"Warnings: {summary.warning_count}",
        ]
    )


def _format_policy_test_result(result) -> str:
    matched_rule = result.matched_rule.name if result.matched_rule else "None"
    lines = [
        "Frying-PAN Policy Test Result",
        f"Scope: {result.scope_path or 'direct rule list'}",
        f"Matched rule: {matched_rule}",
        f"Action: {result.action}",
        f"Evaluated rules: {result.evaluated_rule_count}",
        f"Later matching rules: {len(result.later_matching_rules)}",
        f"Warnings: {len(result.warnings)}",
    ]
    return "\n".join(lines)


def _format_policy_audit_result(result) -> str:
    lines = [
        "Frying-PAN Policy Audit Result",
        f"Source type: {result.source_type or 'unknown'}",
        f"Scope: {result.scope_path or 'all audited scopes'}",
        f"Audited rules: {result.audited_rule_count}",
        f"Findings: {result.finding_count}",
        f"Warnings: {len(result.warnings)}",
    ]
    if result.finding_counts_by_severity:
        counts = ", ".join(
            f"{severity}={count}"
            for severity, count in sorted(result.finding_counts_by_severity.items())
        )
        lines.append(f"Severity counts: {counts}")
    return "\n".join(lines)


def _format_dedupe_analysis_result(result) -> str:
    lines = [
        "Frying-PAN Dedupe And Conflict Analysis",
        f"Source type: {result.source_type or 'unknown'}",
        f"Analyzed objects: {result.analyzed_object_count}",
        f"Findings: {result.finding_count}",
        f"Warnings: {len(result.warnings)}",
    ]
    if result.finding_counts_by_severity:
        counts = ", ".join(
            f"{severity}={count}"
            for severity, count in sorted(result.finding_counts_by_severity.items())
        )
        lines.append(f"Severity counts: {counts}")
    return "\n".join(lines)


def _format_modify_plan(plan) -> str:
    return "\n".join(
        [
            "Frying-PAN Modify Plan",
            f"Source type: {plan.source_type or 'unknown'}",
            f"Status: {plan.status.value}",
            f"Actions: {plan.action_count}",
            f"Validation messages: {len(plan.validation.messages)}",
            "XML export: blocked",
        ]
    )


def _format_migration_plan(plan) -> str:
    return "\n".join(
        [
            "Frying-PAN Migration Plan",
            f"Source type: {plan.source_type or 'unknown'}",
            f"Target type: {plan.target_type or 'unknown'}",
            f"Status: {plan.status.value}",
            f"Mappings: {plan.mapping_count}",
            f"Decisions: {plan.decision_count}",
            f"Validation messages: {len(plan.validation.messages)}",
            "XML export: blocked",
        ]
    )


def _format_conversion_package(package, plan) -> str:
    return "\n".join(
        [
            "Frying-PAN Conversion Package",
            f"Source format: {package.source_format}",
            f"Source config ID: {package.normalized_config.source_id}",
            f"Scopes: {package.scope_count}",
            f"Entities: {package.entity_count}",
            f"Security rules: {package.security_rule_count}",
            f"Warnings: {package.warning_count}",
            f"Unsupported features: {package.unsupported_count}",
            f"Validation errors: {len(package.validation.errors)}",
            f"Plan decisions: {plan.decision_count}",
            "XML export: blocked",
        ]
    )


if __name__ == "__main__":
    raise SystemExit(main())
