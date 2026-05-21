from __future__ import annotations

import argparse
import sys
from pathlib import Path

from frying_pan.analysis.inventory import summarize_inventory
from frying_pan.export.report_exporter import export_inventory_markdown
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


if __name__ == "__main__":
    raise SystemExit(main())
