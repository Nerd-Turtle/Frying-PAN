<p align="center">
  <img src="assets/branding/logo-readme.png" alt="Frying-PAN logo">
</p>

# Frying-PAN

Frying-PAN is an offline desktop workbench for analyzing, modifying,
migrating, converting, and validating Palo Alto Networks Panorama / PAN-OS
configuration exports.

The default workflow is local:

1. Download or build the app.
2. Run it on your workstation.
3. Open or import configuration files.
4. Analyze, audit, stage modifications or migration decisions.
5. Export local reports first, and XML artifacts later after serializer
   validation is reliable.

No hosted server, Docker deployment, external database, login system, or
multi-user web application is required for normal use.

## Status

This branch is a foundation rebuild. It intentionally does not claim to be a
production Panorama merge engine or XML mutator yet.

Current focus:

- Python 3.12+ desktop app shell with PySide6.
- Portable local project folders.
- Source import and source detection for Panorama and standalone firewall XML.
- Phase 1 normalized inventory parsing for common PAN-OS objects and security
  rules.
- Reference/dependency extraction foundation for inventory reports and future
  policy workflows.
- Policy tester, audit, and assurance foundations.
- CLI entry points for detection, inventory summaries, and Markdown reports.

XML export and mutation will be added carefully after parser and serializer
tests are strong enough to support it.

## Why Offline First?

Firewall and Panorama exports are sensitive. Frying-PAN is designed for
engineers who need to inspect and plan changes without uploading configuration
data to a hosted service or standing up application infrastructure.

Projects are portable local folders:

```text
Frying-PAN-Project/
  frying-pan.project.json
  sources/
    panorama-prod.xml
    firewall-branch.xml
  cache/
    parsed.sqlite
  exports/
    report.md
  logs/
    frying-pan.log
```

SQLite is used as a local cache/index inside a project workspace, not as an
external application database.

## Product Workflows

- **Modify**: analyze and stage changes for a single Palo Alto XML
  configuration.
- **Migrate**: map and plan movement or merging between Palo Alto XML
  configurations.
- **Convert**: parse non-Palo Alto source material into a normalized
  Palo-compatible import package for later review.
- **Policy Audit / Policy Assurance**: detect policy risks and compare intended
  behavior before and after planned changes.
- **Policy Tester**: evaluate a single flow against normalized rule data and
  explain matching behavior conservatively.

## Repository Layout

```text
frying_pan/
  app.py                     # PySide6 application entry point
  gui/                       # Thin desktop UI shell and workspaces
  sources/                   # Source adapters and type detection
  normalized/                # Canonical internal models
  panos/                     # PAN-OS helpers, normalizers, serializers
  policy/                    # Match, audit, and assurance foundations
  workflows/                 # Modify, migrate, and convert plan models
  storage/                   # Portable project workspace and SQLite cache
  cli/                       # CLI entry points
tests/
  fixtures/
docs/devel/
```

## Local Development

Use Python 3.12 or newer.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
.venv/bin/python -m pytest
.venv/bin/python -m ruff check .
```

Run the desktop shell:

```bash
frying-pan-gui
```

Run the CLI skeleton:

```bash
.venv/bin/python -m frying_pan.cli.main detect path/to/source.xml
.venv/bin/python -m frying_pan.cli.main inventory path/to/source.xml
.venv/bin/python -m frying_pan.cli.main inventory path/to/source.xml --json
.venv/bin/python -m frying_pan.cli.main inventory path/to/source.xml --report-md report.md
.venv/bin/python -m frying_pan.cli.main workspace-create ./Frying-PAN-Project --name "Lab Migration"
```

## Design Principles

- Keep GUI logic thin and workflow-focused.
- Keep parsing, normalization, policy logic, dependency analysis, and plan
  behavior in GUI-independent Python modules.
- Treat raw XML as an import/export boundary, not the primary internal model.
- Prefer conservative analysis and explicit warnings over hidden assumptions.
- Do not claim production-safe XML export until serializer tests exist.
- Use official Palo Alto Networks documentation when encoding PAN-OS or
  Panorama behavior.

Read [AGENTS.md](AGENTS.md) before making architectural changes.
