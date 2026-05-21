from __future__ import annotations

import argparse
import sys
from pathlib import Path

from frying_pan.analysis.inventory import summarize_inventory
from frying_pan.export.policy_audit_exporter import export_policy_audit_markdown
from frying_pan.export.policy_test_exporter import export_policy_test_markdown
from frying_pan.export.report_exporter import export_inventory_markdown
from frying_pan.policy.audit.audit_engine import PolicyAuditEngine
from frying_pan.policy.match.match_engine import PolicyMatchEngine
from frying_pan.policy.match.test_case import PolicyTestCase
from frying_pan.sources.detection import detect_source
from frying_pan.sources.parsing import SourceParseError, parse_source
from frying_pan.storage.workspace import ProjectWorkspace


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


if __name__ == "__main__":
    raise SystemExit(main())
