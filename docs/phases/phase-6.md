# Phase 6: Migrate Plan

Status: planned

## Goal

Stage migration decisions between Palo Alto source and target configurations,
including scope mapping, object mapping, zone mapping, rule placement,
dependency inclusion, conflict handling, and policy assurance comparison before
any export is considered.

Phase 6 is about planning and assurance for Palo Alto to Palo Alto migration or
merge workflows. It must not mutate source or target XML directly.

## Execution Model

Phase 6 is expected to be implemented through multiple Tasks.

Each Codex prompt/session may complete one or more Tasks, but the Phase remains
planned or active until all Tasks are complete and final Phase 6 validation
passes.

When implementing Phase 6:

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

1. Migration behavior notes
2. Migration plan model
3. Source and target workspace binding
4. Scope mapping
5. Zone mapping
6. Object mapping
7. Rule placement mapping
8. Dependency inclusion and conflict handling
9. Policy assurance integration
10. Migration preview/diff model
11. CLI migrate-plan command
12. GUI Migrate workspace
13. Markdown/JSON migration report export
14. Tests and validation

## Task Status Values

Use these statuses consistently:

- planned
- in-progress
- blocked
- complete

A Task cannot be marked complete unless its validation criteria are satisfied.

## Tasks

### Task 6.1: Migration Behavior Notes

Status: planned

Goal:

Document how Frying-PAN stages migration decisions and where offline migration
assurance is limited.

Implementation Notes:

- Create or update `docs/migrate-plan-notes.md`.
- Define source, target, scope mapping, object mapping, zone mapping, rule
  placement, dependency inclusion, and assurance terminology.
- Document that migration plans do not mutate source or target XML.
- Reference official Panorama Device Group and object behavior where encoded.

Validation:

- Notes exist and match implemented behavior.
- `pytest` passes if code changed.
- `ruff check .` passes if code changed.

Completion Criteria:

- Migration limitations and staged workflow are clear.

### Task 6.2: Migration Plan Model

Status: planned

Goal:

Define the root Migration plan model for source-to-target planning.

Implementation Notes:

- Include source ID, target ID, mappings, staged rule/object decisions,
  dependency decisions, assurance results, validation results, warnings, and
  plan status.
- Keep model GUI-independent.

Validation:

- Unit tests instantiate and serialize migration plans.
- Existing migration plan skeleton tests are updated.
- `pytest` passes.
- `ruff check .` passes.

Completion Criteria:

- Migration plans are structured and reusable by CLI/GUI/tests.

### Task 6.3: Source And Target Workspace Binding

Status: planned

Goal:

Represent source and target imported configurations in a local project
workspace for migration planning.

Implementation Notes:

- Support selecting one source and one target normalized config.
- Preserve source/target metadata and checksums.
- Do not require hosted services or multi-user state.

Validation:

- Tests cover binding two imported sources to a migration plan.
- Workspace persistence tests pass if persistence is implemented.
- `pytest` passes.
- `ruff check .` passes.

Completion Criteria:

- Migration plans can identify source and target configs deterministically.

### Task 6.4: Scope Mapping

Status: planned

Goal:

Stage source-to-target scope mappings.

Implementation Notes:

- Support Device Group, Shared, and vsys scope mappings where parsed.
- Validate mapping compatibility.
- Warn for Panorama hierarchy and local firewall context limitations.

Validation:

- Tests cover valid and invalid scope mappings.
- Tests cover unmapped scope warnings.
- `pytest` passes.
- `ruff check .` passes.

Completion Criteria:

- Scope mapping is explicit and validation-backed.

### Task 6.5: Zone Mapping

Status: planned

Goal:

Stage source-to-target zone mappings for rule migration and assurance.

Implementation Notes:

- Support explicit one-to-one mappings.
- Preserve unmapped zone warnings.
- Do not infer zones from routing unless explicitly implemented and tested.

Validation:

- Tests cover explicit zone mappings.
- Tests cover missing mappings.
- `pytest` passes.
- `ruff check .` passes.

Completion Criteria:

- Zone decisions are explicit and never guessed.

### Task 6.6: Object Mapping

Status: planned

Goal:

Stage source-to-target object mapping decisions.

Implementation Notes:

- Support create-new, reuse-existing, rename, merge, and skip modes where
  existing skeletons allow.
- Use Phase 4 dedupe/conflict findings where practical.
- Validate object type and scope compatibility.

Validation:

- Tests cover supported mapping modes.
- Tests cover conflict warnings.
- Tests cover invalid mapping rejection.
- `pytest` passes.
- `ruff check .` passes.

Completion Criteria:

- Object mapping is structured, validated, and reviewable.

### Task 6.7: Rule Placement Mapping

Status: planned

Goal:

Stage target rulebase placement for migrated rules.

Implementation Notes:

- Support target scope, rulebase type, before/after anchors, and append modes
  where practical.
- Preserve Panorama pre/post/local boundaries.
- Warn when target anchors are missing or ambiguous.

Validation:

- Tests cover append and anchored placement.
- Tests cover blocked cross-boundary placement.
- `pytest` passes.
- `ruff check .` passes.

Completion Criteria:

- Rule placement decisions are deterministic and traceable.

### Task 6.8: Dependency Inclusion And Conflict Handling

Status: planned

Goal:

Include required object dependencies and report conflicts before migration plans
can be marked ready.

Implementation Notes:

- Use Phase 1 dependency records where practical.
- Include nested object/service group dependencies.
- Surface name conflicts and unresolved references.
- Avoid automatic conflict resolution unless explicitly staged.

Validation:

- Tests cover dependency inclusion.
- Tests cover conflict findings.
- Tests cover unresolved dependency warnings.
- `pytest` passes.
- `ruff check .` passes.

Completion Criteria:

- Migration plans cannot silently omit required dependencies.

### Task 6.9: Policy Assurance Integration

Status: planned

Goal:

Compare before/after behavior for selected test flows using Phase 2 policy
testing primitives.

Implementation Notes:

- Support operator-provided test flows.
- Compare matched rule/action before and after staged mapping decisions where
  practical.
- Emit warnings where staged plans cannot be fully simulated offline.

Validation:

- Tests cover unchanged and changed behavior snapshots.
- Tests cover warning behavior for unsupported comparisons.
- `pytest` passes.
- `ruff check .` passes.

Completion Criteria:

- Migration plans can include behavior comparison evidence.

### Task 6.10: Migration Preview And Diff Model

Status: planned

Goal:

Provide a human-readable preview of staged migration decisions.

Implementation Notes:

- Summarize scope, zone, object, rule, dependency, and assurance decisions.
- Include conflicts and warnings.
- Do not generate production XML output in Phase 6 unless serializer tests are
  explicitly added and completed.

Validation:

- Tests cover preview generation.
- Preview labels export limitations.
- `pytest` passes.
- `ruff check .` passes.

Completion Criteria:

- Operators can review migration decisions before future export work.

### Task 6.11: CLI Migrate Plan Command

Status: planned

Goal:

Expose migration plan creation, validation, and reporting through the CLI.

Implementation Notes:

- Add command group or commands for migration planning if practical.
- Support JSON plan output.
- Support Markdown report output.
- Keep command focused on staging/reporting, not XML mutation.

Validation:

- CLI command works against source and target fixtures.
- Invalid mapping returns useful non-zero result.
- `pytest` passes.
- `ruff check .` passes.

Completion Criteria:

- CLI uses the same core migration models as GUI and tests.

### Task 6.12: GUI Migrate Workspace

Status: planned

Goal:

Make the Migrate workspace display source/target trees, mappings, staged
decisions, validation warnings, and preview output.

Implementation Notes:

- Keep drag/drop operations staging-only.
- Do not mutate source or target XML from GUI operations.
- Display mapping and validation state clearly.

Validation:

- Offscreen GUI construction test passes.
- GUI tests cover mapping display where practical.
- `pytest` passes.
- `ruff check .` passes.

Completion Criteria:

- GUI presents migration as staged decisions.

### Task 6.13: Migration Report Export

Status: planned

Goal:

Export migration plans for review.

Implementation Notes:

- Support JSON serialization.
- Support Markdown report export.
- Include source/target summary, mappings, staged decisions, dependency
  inclusion, assurance results, validation warnings, and limitations.
- Do not imply XML mutation/export safety.

Validation:

- Tests verify JSON serialization.
- Tests verify Markdown report generation if implemented.
- `pytest` passes.
- `ruff check .` passes.

Completion Criteria:

- Migration plans can be saved locally for review.

### Task 6.14: Final Phase 6 Validation

Status: planned

Goal:

Confirm Phase 6 is complete, tested, documented, and consistent with
architecture guardrails.

Validation:

- `pytest` passes.
- `ruff check .` passes.
- Existing CLI commands still work against fixtures.
- Migration CLI validation/report command works if implemented.
- Offscreen GUI construction passes.
- Migration GUI/model tests pass.
- Migration report export tests pass if export is implemented.
- `docs/migrate-plan-notes.md` is updated.
- Source and target XML mutation remain blocked.

Completion Criteria:

- Every Phase 6 Task is complete.
- Full Phase 6 validation suite passes.
- Validation evidence is recorded.

## Phase 6 Completion Rules

A task cannot be marked complete unless its validation criteria are satisfied.

A phase cannot be marked complete unless all tasks are complete and the full
validation suite passes.

## Architecture Guardrails

- Drag/drop and mapping operations create staged decisions first.
- Do not mutate source or target XML directly.
- Keep migration logic in GUI-independent workflow modules.
- Keep policy assurance conservative and warning-rich.
- Keep export claims conservative until serializer tests exist.
