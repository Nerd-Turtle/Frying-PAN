from __future__ import annotations

import argparse
from pathlib import Path

from frying_pan.sources.detection import detect_source
from frying_pan.storage.workspace import ProjectWorkspace


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="frying-pan")
    subparsers = parser.add_subparsers(dest="command", required=True)

    detect_parser = subparsers.add_parser("detect", help="Detect a source configuration type.")
    detect_parser.add_argument("source", type=Path)

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


if __name__ == "__main__":
    raise SystemExit(main())
