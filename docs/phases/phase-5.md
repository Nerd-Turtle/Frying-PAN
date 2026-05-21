# Phase 5: Modify Plan

Status: complete

## Goal

Stage single-configuration modification decisions such as object rename, object
dedupe, object move, rule reorder, rule cleanup, and rule metadata changes
without mutating source XML directly.

Phase 5 is about planning, review, and local report generation. It must not
claim production-safe XML export until parser and serializer tests exist.

## Execution Model

Phase 5 is expected to be implemented through multiple Tasks.

Each Codex prompt/session may complete one or more Tasks, but the Phase remains
planned or active until all Tasks are complete and final Phase 5 validation
passes.

When implementing Phase 5:

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

1. Modify behavior notes
2. Modify plan model
3. Plan action model
4. Plan validation and dependency checks
5. Object rename staging
6. Object dedupe staging
7. Object move staging
8. Rule reorder and metadata staging
9. Preview/diff model
10. CLI modify-plan command
11. GUI Modify workspace
12. Markdown/JSON modify report export
13. Tests and validation

## Task Status Values

Use these statuses consistently:

- planned
- in-progress
- blocked
- complete

A Task cannot be marked complete unless its validation criteria are satisfied.

## Phase 5 Validation Evidence

- `pytest -q` passed with 72 tests.
- `ruff check .` passed.
- Existing CLI commands still worked against fixtures.
- CLI `modify-plan` worked against the firewall fixture.
- Modify GUI/model tests passed offscreen.
- Modify Markdown export tests passed.
- `docs/modify-plan-notes.md` was created with official Palo Alto Networks
  references and current staging/export limitations.
- Source XML mutation remains blocked.

## Tasks

### Task 5.1: Modify Behavior Notes

Status: complete

Validation Evidence:

- `docs/modify-plan-notes.md` created and aligned to implemented staged-plan
  behavior.
- `pytest -q` passed with 72 tests.
- `ruff check .` passed.

Goal:

Document how Frying-PAN stages single-configuration modifications and what is
intentionally not exported in Phase 5.

Implementation Notes:

- Create or update `docs/modify-plan-notes.md`.
- Explain staged decisions, dependencies, warnings, and review workflow.
- Explain that source XML is not mutated during GUI drag/drop or staging.
- Explain export limitations until serializer tests exist.

Validation:

- Notes exist and match implemented behavior.
- `pytest` passes if code changed.
- `ruff check .` passes if code changed.

Completion Criteria:

- Operators can understand staged Modify plans versus XML changes.

### Task 5.2: Modify Plan Model

Status: complete

Validation Evidence:

- `ModificationPlan`, plan status, validation, warnings, notes, and computed
  counts implemented.
- Tests cover plan serialization and computed action counts.
- `pytest -q` passed with 72 tests.
- `ruff check .` passed.

Goal:

Define the root Modify plan model for one imported PAN-OS source.

Implementation Notes:

- Include plan ID, source ID, source metadata, status, actions, warnings,
  validation results, and timestamps if useful.
- Keep model GUI-independent.
- Persist only local plan state in project workspaces if persistence is
  implemented.

Validation:

- Unit tests instantiate and serialize Modify plans.
- Existing plan skeleton tests are updated.
- `pytest` passes.
- `ruff check .` passes.

Completion Criteria:

- Modify plans are structured and reusable by CLI/GUI/tests.

### Task 5.3: Modify Action Model

Status: complete

Validation Evidence:

- Staged action models support rename, dedupe, move, reorder, and rule metadata
  changes.
- Invalid action shape validation is tested.
- `pytest -q` passed with 72 tests.
- `ruff check .` passed.

Goal:

Define staged action models for supported single-configuration changes.

Implementation Notes:

- Support object rename, object dedupe/replace reference, object move, rule
  reorder, rule disable/enable, and rule metadata/logging changes if practical.
- Include action status, target scope, affected objects/rules, dependencies,
  warnings, and operator notes.
- Keep unsupported action types explicit.

Validation:

- Tests cover each implemented action type.
- Invalid actions fail validation.
- `pytest` passes.
- `ruff check .` passes.

Completion Criteria:

- Actions are explicit enough for review and future export.

### Task 5.4: Plan Validation And Dependency Checks

Status: complete

Validation Evidence:

- Plan validation checks duplicate staged sources, missing source objects,
  action warnings, and unresolved imported references.
- Tests cover valid and blocked plans.
- `pytest -q` passed with 72 tests.
- `ruff check .` passed.

Goal:

Validate Modify plans before they can be marked ready for review.

Implementation Notes:

- Check unresolved references.
- Check object dependency impact.
- Check duplicate action conflicts.
- Check scope compatibility.
- Emit warnings for unparsed or unsupported sections.

Validation:

- Tests cover valid and invalid plans.
- Tests cover dependency warnings.
- `pytest` passes.
- `ruff check .` passes.

Completion Criteria:

- Plans cannot silently contain contradictory staged actions.

### Task 5.5: Object Rename Staging

Status: complete

Validation Evidence:

- Object rename staging records source/target references and impacted parsed
  references.
- Tests cover rename staging and impacted reference listing.
- `pytest -q` passed with 72 tests.
- `ruff check .` passed.

Goal:

Stage object rename decisions and impacted reference updates without mutating
XML.

Implementation Notes:

- Support address, address group, service, service group, and tags where
  parser coverage exists.
- Record impacted references.
- Warn for unsupported/unparsed references.

Validation:

- Tests cover rename action creation.
- Tests cover impacted reference listing.
- Tests cover duplicate target name validation.
- `pytest` passes.
- `ruff check .` passes.

Completion Criteria:

- Rename plans are reviewable and dependency-aware.

### Task 5.6: Object Dedupe Staging

Status: complete

Validation Evidence:

- Object dedupe staging records duplicate and canonical object references plus
  impacted references.
- Tests cover dedupe action creation.
- `pytest -q` passed with 72 tests.
- `ruff check .` passed.

Goal:

Stage replacement of duplicate objects with a chosen canonical object.

Implementation Notes:

- Consume Phase 4 duplicate findings where practical.
- Record references that would be updated.
- Preserve original object and canonical object identities.
- Warn when references are incomplete.

Validation:

- Tests cover dedupe action creation from duplicate findings.
- Tests cover reference impact summary.
- `pytest` passes.
- `ruff check .` passes.

Completion Criteria:

- Dedupe actions are explicit and reversible at plan level.

### Task 5.7: Object Move Staging

Status: complete

Validation Evidence:

- Object move staging validates target scope existence, target object conflicts,
  and Panorama inheritance/override review warnings.
- Tests cover object move staging.
- `pytest -q` passed with 72 tests.
- `ruff check .` passed.

Goal:

Stage moving an object between supported scopes without mutating XML.

Implementation Notes:

- Validate target scope compatibility.
- Preserve warnings for Panorama inheritance and object override behavior.
- Record affected references.

Validation:

- Tests cover allowed moves.
- Tests cover blocked moves.
- Tests cover scope warnings.
- `pytest` passes.
- `ruff check .` passes.

Completion Criteria:

- Object move plans are conservative and scope-aware.

### Task 5.8: Rule Reorder And Metadata Staging

Status: complete

Validation Evidence:

- Rule reorder and rule metadata staging implemented inside existing scope and
  rulebase context.
- Tests cover same-rulebase reorder and enabled/logging metadata staging.
- `pytest -q` passed with 72 tests.
- `ruff check .` passed.

Goal:

Stage rule order and simple rule metadata changes.

Implementation Notes:

- Support reorder within the same rulebase and scope.
- Support staged enable/disable and logging metadata changes if practical.
- Do not move rules across Panorama pre/post/local boundaries unless explicitly
  implemented and tested.

Validation:

- Tests cover same-rulebase reorder.
- Tests cover blocked cross-boundary reorder.
- Tests cover metadata changes if implemented.
- `pytest` passes.
- `ruff check .` passes.

Completion Criteria:

- Rule changes preserve policy ordering assumptions and warnings.

### Task 5.9: Preview And Diff Model

Status: complete

Validation Evidence:

- `ModifyPlanPreview` summarizes staged actions and impacted references while
  keeping XML export blocked.
- Tests cover preview generation and export-blocked state.
- `pytest -q` passed with 72 tests.
- `ruff check .` passed.

Goal:

Provide a human-readable preview of staged Modify actions.

Implementation Notes:

- Generate action summaries and affected-reference summaries.
- Provide before/after normalized model snippets where practical.
- Do not generate production XML output in Phase 5 unless serializer tests are
  explicitly added and completed.

Validation:

- Tests cover preview generation.
- Preview labels XML export limitations.
- `pytest` passes.
- `ruff check .` passes.

Completion Criteria:

- Operators can review staged actions before future export work.

### Task 5.10: CLI Modify Plan Command

Status: complete

Validation Evidence:

- `frying-pan modify-plan` added with staged rename, move, dedupe, reorder,
  JSON output, and Markdown report output.
- CLI modify-plan worked against the firewall fixture.
- `tests/test_cli_inventory.py` covers JSON and Markdown output.
- `pytest -q` passed with 72 tests.
- `ruff check .` passed.

Goal:

Expose Modify plan creation, validation, and reporting through the CLI.

Implementation Notes:

- Add command group or commands for creating and validating plan files if
  practical.
- Support JSON plan output.
- Support Markdown report output.
- Keep command focused on staging/reporting, not XML mutation.

Validation:

- CLI command works against fixture source.
- Invalid plan returns useful non-zero result.
- `pytest` passes.
- `ruff check .` passes.

Completion Criteria:

- CLI uses the same core Modify plan models as GUI and tests.

### Task 5.11: GUI Modify Workspace

Status: complete

Validation Evidence:

- Modify GUI now displays staged plan summary and action table from core models.
- `tests/test_gui_modify.py` passed offscreen.
- `pytest -q` passed with 72 tests.
- `ruff check .` passed.

Goal:

Make the Modify workspace display source inventory, staged actions, validation
warnings, and preview output.

Implementation Notes:

- Keep GUI drag/drop and controls staging-only.
- Do not mutate source XML from GUI operations.
- Display plan validation state.

Validation:

- Offscreen GUI construction test passes.
- GUI tests cover staged action display where practical.
- `pytest` passes.
- `ruff check .` passes.

Completion Criteria:

- GUI presents Modify plans as staged decisions.

### Task 5.12: Modify Report Export

Status: complete

Validation Evidence:

- Modify plans serialize to JSON through Pydantic models.
- Markdown export added in `frying_pan/export/modify_plan_exporter.py`.
- Modify report export tests passed.
- `pytest -q` passed with 72 tests.
- `ruff check .` passed.

Goal:

Export Modify plans for review.

Implementation Notes:

- Support JSON serialization.
- Support Markdown report export.
- Include source summary, staged actions, impacted references, validation
  warnings, and limitations.
- Do not imply XML mutation/export safety.

Validation:

- Tests verify JSON serialization.
- Tests verify Markdown report generation if implemented.
- `pytest` passes.
- `ruff check .` passes.

Completion Criteria:

- Modify plans can be saved locally for review.

### Task 5.13: Final Phase 5 Validation

Status: complete

Validation Evidence:

- `pytest -q` passed with 72 tests.
- `ruff check .` passed.
- Existing CLI commands still worked against fixtures.
- CLI modify-plan worked against the firewall fixture.
- Modify GUI/model and report export tests passed.
- `docs/modify-plan-notes.md` and roadmap references were updated.
- Source XML mutation remains blocked.

Goal:

Confirm Phase 5 is complete, tested, documented, and consistent with
architecture guardrails.

Validation:

- `pytest` passes.
- `ruff check .` passes.
- Existing CLI commands still work against fixtures.
- Modify CLI validation/report command works if implemented.
- Offscreen GUI construction passes.
- Modify GUI/model tests pass.
- Modify report export tests pass if export is implemented.
- `docs/modify-plan-notes.md` is updated.
- Source XML mutation remains blocked.

Completion Criteria:

- Every Phase 5 Task is complete.
- Full Phase 5 validation suite passes.
- Validation evidence is recorded.

## Phase 5 Completion Rules

A task cannot be marked complete unless its validation criteria are satisfied.

A phase cannot be marked complete unless all tasks are complete and the full
validation suite passes.

## Architecture Guardrails

- Drag/drop and GUI operations create staged decisions first.
- Do not mutate source XML directly.
- Keep plan logic in GUI-independent workflow modules.
- Keep export claims conservative until serializer tests exist.
- Prefer explicit validation warnings over generated guesses.
