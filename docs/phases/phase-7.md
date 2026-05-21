# Phase 7: Convert Framework

Status: planned

## Goal

Define a normalized import package framework so future non-Palo Alto source
material can be converted into Palo-compatible planning inputs for Modify or
Migrate workflows without directly mutating Panorama XML.

Phase 7 is about conversion structure, validation, warnings, and adapter
contracts. It is not about claiming feature-complete third-party vendor
conversion.

## Execution Model

Phase 7 is expected to be implemented through multiple Tasks.

Each Codex prompt/session may complete one or more Tasks, but the Phase remains
planned or active until all Tasks are complete and final Phase 7 validation
passes.

When implementing Phase 7:

- choose the next planned Task
- mark it in-progress before implementation
- implement the Task
- run task-specific validation
- update tests/docs as needed
- mark the Task complete only if validation passes
- leave the Phase status active until all Tasks are complete

If a Task grows too large, split it into smaller Tasks inside this phase
document instead of rushing or over-scoping the session.

## Scope

Functional areas:

1. Conversion behavior notes
2. Normalized import package schema
3. Conversion warning model
4. Vendor adapter contract
5. CSV/JSON generic adapter if practical
6. Palo-compatible object normalization
7. Palo-compatible rule normalization
8. Validation and gap reporting
9. Convert plan model integration
10. CLI convert command
11. GUI Convert workspace
12. Markdown/JSON conversion report export
13. Tests and validation

## Task Status Values

Use these statuses consistently:

- planned
- in-progress
- blocked
- complete

A Task cannot be marked complete unless its validation criteria are satisfied.

## Tasks

### Task 7.1: Conversion Behavior Notes

Status: planned

Goal:

Document how conversion inputs become normalized Palo-compatible planning data
and where vendor-specific behavior remains unsupported.

Implementation Notes:

- Create or update `docs/convert-framework-notes.md`.
- Define Convert versus Migrate versus Modify terminology.
- Explain normalized import packages, adapter warnings, and unsupported
  semantics.
- Explain that conversion output feeds planning workflows and does not mutate
  Panorama XML directly.

Validation:

- Notes exist and match implemented behavior.
- `pytest` passes if code changed.
- `ruff check .` passes if code changed.

Completion Criteria:

- Conversion scope and limitations are clear.

### Task 7.2: Normalized Import Package Schema

Status: planned

Goal:

Define a portable package schema for converted source material.

Implementation Notes:

- Include package metadata, source metadata, scopes, objects, services, rules,
  references, warnings, and unsupported item records.
- Prefer Pydantic models with stable JSON serialization.
- Keep schema separate from raw vendor files.

Validation:

- Tests instantiate and serialize packages.
- Invalid packages fail validation.
- `pytest` passes.
- `ruff check .` passes.

Completion Criteria:

- Converted inputs can be exchanged as local JSON-like packages.

### Task 7.3: Conversion Warning Model

Status: planned

Goal:

Represent unsupported, lossy, ambiguous, and review-required conversion
conditions.

Implementation Notes:

- Include severity, source location, source field, normalized target, message,
  and suggested review.
- Keep warnings attached to packages and individual converted entities where
  useful.

Validation:

- Tests cover warning serialization.
- Tests cover warnings attached to package and entity records.
- `pytest` passes.
- `ruff check .` passes.

Completion Criteria:

- Conversion gaps are structured and visible.

### Task 7.4: Vendor Adapter Contract

Status: planned

Goal:

Define the interface future vendor adapters must implement.

Implementation Notes:

- Include detection, parse, normalize, warning emission, and package output
  responsibilities.
- Keep adapters offline and local-file based.
- Avoid committing to specific vendor feature completeness in the framework.

Validation:

- Tests cover a fake adapter implementing the contract.
- Invalid adapter outputs fail validation.
- `pytest` passes.
- `ruff check .` passes.

Completion Criteria:

- Future adapters have a clear contract.

### Task 7.5: Generic CSV/JSON Adapter

Status: planned

Goal:

Implement a small generic adapter if practical to prove the conversion
framework end to end.

Implementation Notes:

- Support a documented minimal CSV or JSON format for addresses, services, and
  security rules.
- Emit warnings for missing fields and unsupported semantics.
- Keep this adapter intentionally generic, not vendor-branded.

Validation:

- Tests cover valid CSV/JSON conversion.
- Tests cover malformed input warnings/errors.
- `pytest` passes.
- `ruff check .` passes.

Completion Criteria:

- The framework has one working offline adapter path if implemented.

### Task 7.6: Palo-Compatible Object Normalization

Status: planned

Goal:

Normalize converted objects into Palo-compatible internal object records.

Implementation Notes:

- Support address objects, address groups, service objects, service groups, and
  tags where practical.
- Preserve unsupported fields as warnings.
- Avoid direct XML serialization.

Validation:

- Tests cover object normalization.
- Tests cover unsupported object warnings.
- `pytest` passes.
- `ruff check .` passes.

Completion Criteria:

- Converted objects can feed analysis and planning workflows.

### Task 7.7: Palo-Compatible Rule Normalization

Status: planned

Goal:

Normalize converted rule records into Palo-compatible internal security rule
records.

Implementation Notes:

- Support source/destination zones, addresses, applications, services, users,
  URL category hints, action, disabled state, tags, and description where
  practical.
- Preserve unsupported criteria as structured warnings.
- Keep rule order deterministic.

Validation:

- Tests cover rule normalization.
- Tests cover rule order preservation.
- Tests cover unsupported criteria warnings.
- `pytest` passes.
- `ruff check .` passes.

Completion Criteria:

- Converted rules can feed Policy Tester, Policy Audit, and planning workflows
  where supported.

### Task 7.8: Validation And Gap Reporting

Status: planned

Goal:

Validate conversion packages and summarize unsupported or lossy conversion
gaps.

Implementation Notes:

- Check required fields.
- Check unresolved converted references.
- Check unsupported object/rule criteria.
- Produce summary counts and warning rollups.

Validation:

- Tests cover valid and invalid packages.
- Tests cover unresolved references and warning summaries.
- `pytest` passes.
- `ruff check .` passes.

Completion Criteria:

- Conversion packages can be reviewed before planning use.

### Task 7.9: Convert Plan Model Integration

Status: planned

Goal:

Connect conversion packages to existing Convert plan skeletons.

Implementation Notes:

- Keep conversion package, plan decisions, and future target mapping separate.
- Allow converted package review before migration planning.
- Preserve warnings and unsupported item records.

Validation:

- Tests cover Convert plan creation from package.
- Tests cover warning propagation.
- `pytest` passes.
- `ruff check .` passes.

Completion Criteria:

- Convert plans can consume normalized import packages.

### Task 7.10: CLI Convert Command

Status: planned

Goal:

Expose conversion package generation and validation through the CLI.

Implementation Notes:

- Add command such as `frying-pan convert path/to/input --format generic-json`.
- Support JSON package output.
- Support summary output and Markdown report output if practical.
- Return useful non-zero errors for invalid input.

Validation:

- CLI convert works against generic fixture if adapter is implemented.
- Invalid input returns useful message.
- JSON output validates against package models.
- `pytest` passes.
- `ruff check .` passes.

Completion Criteria:

- CLI uses the same conversion framework as GUI and tests.

### Task 7.11: GUI Convert Workspace

Status: planned

Goal:

Make the Convert workspace display source import status, converted package
contents, warnings, and validation results.

Implementation Notes:

- Keep GUI as presentation and workflow orchestration.
- Do not embed adapter logic in GUI classes.
- Display unsupported conversion gaps clearly.

Validation:

- Offscreen GUI construction test passes.
- GUI tests cover package/warning display where practical.
- `pytest` passes.
- `ruff check .` passes.

Completion Criteria:

- GUI can present conversion package results.

### Task 7.12: Conversion Report Export

Status: planned

Goal:

Export conversion results for review.

Implementation Notes:

- Support JSON package output.
- Support Markdown report export.
- Include source summary, converted counts, warnings, unsupported items, and
  limitations.
- Do not imply direct XML export or feature-complete vendor migration.

Validation:

- Tests verify JSON serialization.
- Tests verify Markdown report generation if implemented.
- `pytest` passes.
- `ruff check .` passes.

Completion Criteria:

- Conversion output can be reviewed locally.

### Task 7.13: Final Phase 7 Validation

Status: planned

Goal:

Confirm Phase 7 is complete, tested, documented, and consistent with
architecture guardrails.

Validation:

- `pytest` passes.
- `ruff check .` passes.
- Existing CLI commands still work against fixtures.
- Convert CLI command works against generic fixtures if implemented.
- Offscreen GUI construction passes.
- Convert GUI/model tests pass.
- Conversion report export tests pass if export is implemented.
- `docs/convert-framework-notes.md` is updated.
- Source XML mutation remains blocked.

Completion Criteria:

- Every Phase 7 Task is complete.
- Full Phase 7 validation suite passes.
- Validation evidence is recorded.

## Phase 7 Completion Rules

A task cannot be marked complete unless its validation criteria are satisfied.

A phase cannot be marked complete unless all tasks are complete and the full
validation suite passes.

## Architecture Guardrails

- Keep adapter and normalization logic in GUI-independent modules.
- Treat converted packages as planning inputs, not XML output.
- Preserve conversion warnings instead of hiding lossy transformations.
- Avoid claiming broad vendor support from a minimal adapter.
- Do not mutate source XML.
