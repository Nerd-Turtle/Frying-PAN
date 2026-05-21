# Frying-PAN Roadmap

## Project Direction

Frying-PAN is an offline-first Python desktop workbench for Palo Alto Networks
Panorama / PAN-OS configuration analysis, modification planning, migration
planning, conversion preparation, policy audit, policy assurance, and policy
testing.

Current architecture direction:

- Offline-first Python desktop app.
- PySide6 GUI for normal operator workflows.
- CLI-supported engine for repeatable parser, analysis, and report validation.
- Portable local project workspaces.
- SQLite local cache/index inside project workspaces.
- Normalized internal model for analysis and planning.
- Raw XML as an import/export boundary.
- XML mutation/export remains blocked until parser and serializer tests exist.
- Policy behavior must be implemented conservatively, validated with tests, and
  documented with official Palo Alto Networks references where practical.

Do not reintroduce FastAPI, Next.js, PostgreSQL, login/auth, Docker-first
deployment, or hosted web architecture unless the project owner explicitly
changes direction.

## Current Status

Phase 0/Foundation is complete based on the validation performed during the
foundation rebuild. Phase 1, PAN-OS Inventory Analyzer, is complete based on the
validation recorded in the phase document. Phase 2, Policy Tester v1, is
complete based on the validation recorded in the phase document.

The project currently has a desktop shell, CLI inventory commands, local
workspace model, source detection, Phase 1 PAN-OS inventory parsers, normalized
models, reference/dependency foundations, report generation, conservative
single-flow policy testing, plan model skeletons, and tests. XML mutation/export
remains blocked.

## Phase and Task Model

The roadmap tracks high-level Phases.

Each linked phase document contains Tasks.

A Phase can span multiple Codex prompts/sessions.

Tasks are the preferred unit of implementation for each prompt/session.

A Phase is complete only when all Tasks in the phase are complete and the full
phase validation suite passes.

A Task is complete only when implementation, tests, validation, and required
documentation updates are complete.

## Phase Summary

| Phase | Name | Status | Detail Doc | Goal |
|---|---|---|---|---|
| 0 | Foundation | Complete | [design.md](design.md) | Establish the offline desktop architecture, package skeleton, GUI shell, CLI skeleton, workspace model, and baseline checks. |
| 1 | PAN-OS Inventory Analyzer | Complete | [phase-1.md](../phases/phase-1.md) | Parse Panorama and standalone firewall XML into normalized inventory, dependencies, CLI output, GUI visibility, and reports. |
| 2 | Policy Tester v1 | Complete | [phase-2.md](../phases/phase-2.md) | Evaluate a single test flow with conservative first-match behavior, trace output, later matches, and warnings. |
| 3 | Policy Audit v1 | Planned | [phase-3.md](../phases/phase-3.md) | Analyze full rulebases for obvious shadows, duplicate rules, broad allows, missing references, and App-ID/service uncertainty. |
| 4 | Dedupe and Conflict Analysis | Planned | [phase-4.md](../phases/phase-4.md) | Detect duplicate objects/services, same-name conflicts, unused candidates, and object placement recommendations. |
| 5 | Modify Plan | Planned | [phase-5.md](../phases/phase-5.md) | Stage object/rule modification decisions and generate modification reports without mutating XML. |
| 6 | Migrate Plan | Planned | [phase-6.md](../phases/phase-6.md) | Stage source-to-target scope, object, zone, and rule mappings with dependency inclusion and policy assurance. |
| 7 | Convert Framework | Planned | [phase-7.md](../phases/phase-7.md) | Define normalized import packages, conversion warnings, and future vendor adapters. |

## Phase 0: Foundation

Status: Complete

Goal:

Establish the new offline-first Python desktop foundation and remove the hosted
web application direction.

Completed scope:

- Python package structure under `frying_pan/`.
- PySide6 desktop app shell.
- Main navigation placeholders.
- CLI skeleton.
- Local project workspace model.
- Source import model.
- Source detection skeleton.
- Normalized model skeleton.
- SQLite cache/index foundation.
- Policy match/audit/assurance module skeletons.
- Modify/Migrate/Convert plan model skeletons.
- README and AGENTS.md updated for the desktop direction.

Validation evidence:

- `pytest` passed with 14 tests.
- `ruff check .` passed.
- Offscreen GUI construction passed and produced `Frying-PAN 9`.
- CLI detection worked against the Panorama fixture.

## Phase 1: PAN-OS Inventory Analyzer

Status: Complete

Detail:

- [docs/phases/phase-1.md](../phases/phase-1.md)

Goal:

Import a Panorama or standalone Palo Alto firewall XML file, detect what it is,
parse common PAN-OS objects/rules into normalized entities, extract
references/dependencies, expose inventory through CLI, and surface basic
inventory results in the GUI.

Phase 1 must not enable XML mutation/export. Markdown and HTML inventory
reports are allowed as early export artifacts.

Completed scope:

- Source detection for Panorama, standalone firewall, unknown PAN-OS, and
  invalid XML.
- Panorama and standalone firewall parser foundations for common objects and
  security rules.
- Virtual-router and advanced-routing firewall reference fixtures.
- Normalized inventory, reference, dependency, and report models.
- CLI inventory summaries, JSON output, and Markdown report export.
- Basic GUI inventory display backed by core normalized models.

Validation evidence is recorded in
[docs/phases/phase-1.md](../phases/phase-1.md).

## Phase 2: Policy Tester v1

Status: Complete

Detail:

- [docs/phases/phase-2.md](../phases/phase-2.md)

Goal:

Evaluate a single user-provided flow against normalized policy data with
first-match behavior, trace output, later matching rules, and warnings for
unsupported or uncertain offline behavior.

Completed scope:

- Shared `PolicyTestCase` flow model for CLI, GUI, tests, and engine use.
- Conservative scope/rulebase selection for standalone firewall and Panorama
  Device Group imports.
- Address, address group, zone, service, service group, application, URL
  category, user, and HIP limitation handling.
- Structured first-match trace output with later matching rules and warnings.
- CLI `policy-test` command with text, JSON, and Markdown report output.
- Policy Tester GUI result and trace display backed by core models.
- Policy tester behavior notes with official Palo Alto Networks references.

Validation evidence is recorded in
[docs/phases/phase-2.md](../phases/phase-2.md).

## Phase 3: Policy Audit v1

Status: Planned

Detail:

- [docs/phases/phase-3.md](../phases/phase-3.md)

Goal:

Analyze a full rulebase for structured findings such as obvious full shadows,
duplicate rules, broad allows, missing object references, App-ID gaps, and
service/application uncertainty.

## Phase 4: Dedupe and Conflict Analysis

Status: Planned

Detail:

- [docs/phases/phase-4.md](../phases/phase-4.md)

Goal:

Detect object and service duplicates, same-name/different-value conflicts,
different-name/same-value candidates, unused objects, and initial object
placement recommendations.

## Phase 5: Modify Plan

Status: Planned

Detail:

- [docs/phases/phase-5.md](../phases/phase-5.md)

Goal:

Stage single-configuration modification actions such as dedupe, rename, object
move, and rule reorder decisions. Generate modification reports. Do not export
mutated XML until serializer validation exists.

## Phase 6: Migrate Plan

Status: Planned

Detail:

- [docs/phases/phase-6.md](../phases/phase-6.md)

Goal:

Stage migration decisions between Palo Alto sources and targets, including
scope mapping, object mapping, zone mapping, rule placement, dependency
inclusion, and policy assurance before export.

## Phase 7: Convert Framework

Status: Planned

Detail:

- [docs/phases/phase-7.md](../phases/phase-7.md)

Goal:

Define normalized import package structure and conversion warning models so
future FortiGate, ASA, CSV, JSON, or other vendor adapters can feed Modify or
Migrate workflows without directly mutating Panorama XML.

## Completion Rules

A Phase may only be marked complete when:

- every Task in that Phase is complete
- every Task has validation evidence
- the full phase validation suite passes
- documentation has been updated to reflect the implemented behavior
- no known blocking issues remain untracked

A Task may only be marked complete when:

- the implementation for that Task is complete
- task-specific validation has passed
- related tests have been added or updated
- documentation has been updated where applicable
- limitations or deferred work are explicitly recorded

Never mark work complete based only on code changes.

## Validation Rules

Use validation evidence appropriate to the Task or Phase, such as:

- `pytest` results
- `ruff check .` results
- CLI command output
- GUI/offscreen construction validation
- parser fixture validation
- report generation validation
- documentation update confirmation

If validation cannot be performed, leave the Task as `blocked` or
`in-progress` and document why.

## Architecture Guardrails

- Keep GUI code thin and workflow-focused.
- Keep parsing, normalization, policy logic, dependency analysis, and plan
  behavior in GUI-independent Python modules.
- Treat raw XML as an import/export boundary, not the internal model.
- Keep SQLite local to portable project workspaces.
- Do not reintroduce hosted web infrastructure without explicit owner request.
- Do not mutate source XML during import, drag/drop, mapping, or plan staging.
- Do not claim production-safe XML export until serializer tests exist.
- Use official Palo Alto Networks documentation for PAN-OS behavior whenever
  practical.
- Emit warnings for uncertain policy behavior instead of silently guessing.
