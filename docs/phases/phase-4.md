# Phase 4: Dedupe And Conflict Analysis

Status: complete

## Goal

Detect duplicate objects and services, same-name/different-value conflicts,
different-name/same-value candidates, unused object candidates, and initial
object placement recommendations across imported PAN-OS scopes.

Phase 4 is about analysis and recommendations. It must not mutate source XML or
stage modification decisions directly; later Modify/Migrate phases decide what
to do with the findings.

## Execution Model

Phase 4 is expected to be implemented through multiple Tasks.

Each Codex prompt/session may complete one or more Tasks, but the Phase remains
planned or active until all Tasks are complete and final Phase 4 validation
passes.

When implementing Phase 4:

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

1. Dedupe/conflict behavior notes
2. Analysis finding model
3. Object identity and fingerprinting
4. Address duplicate detection
5. Service duplicate detection
6. Same-name conflict detection
7. Unused object candidate detection
8. Scope placement recommendations
9. CLI dedupe/conflict command
10. GUI analysis display
11. Markdown/JSON report export
12. Tests and validation

## Task Status Values

Use these statuses consistently:

- planned
- in-progress
- blocked
- complete

A Task cannot be marked complete unless its validation criteria are satisfied.

## Phase 4 Validation Evidence

- `pytest -q` passed with 65 tests.
- `ruff check .` passed.
- CLI dedupe-analysis worked against Panorama and firewall fixtures.
- Dedupe/conflict GUI/model tests passed offscreen.
- Dedupe/conflict Markdown export tests passed.
- `docs/dedupe-conflict-notes.md` was created with official Palo Alto Networks
  references and current analysis limitations.
- XML mutation/export remains blocked.

## Tasks

### Task 4.1: Dedupe And Conflict Notes

Status: complete

Validation Evidence:

- `docs/dedupe-conflict-notes.md` created and aligned to implemented analysis
  behavior.
- `pytest -q` passed with 65 tests.
- `ruff check .` passed.

Goal:

Document the meaning, limitations, and safe handling of dedupe/conflict
analysis findings.

Implementation Notes:

- Create or update `docs/dedupe-conflict-notes.md`.
- Explain same-name conflict, exact duplicate, equivalent duplicate, unused
  candidate, and placement recommendation terminology.
- Explain Panorama Shared versus Device Group scope limitations and object
  override uncertainty.

Validation:

- Notes exist and match implemented behavior.
- `pytest` passes if code changed.
- `ruff check .` passes if code changed.

Completion Criteria:

- Operators can distinguish findings from staged changes.

### Task 4.2: Dedupe Finding Model

Status: complete

Validation Evidence:

- `DedupeFinding`, `ObjectFingerprint`, and `DedupeAnalysisResult` added.
- Tests cover model serialization through JSON CLI output and report export.
- `pytest -q` passed with 65 tests.
- `ruff check .` passed.

Goal:

Define structured models for dedupe, conflict, unused, and placement findings.

Implementation Notes:

- Include finding type, severity, object type, object names, scopes,
  fingerprints, explanation, warnings, and recommended review action.
- Keep models GUI-independent.

Validation:

- Unit tests instantiate and serialize findings.
- `pytest` passes.
- `ruff check .` passes.

Completion Criteria:

- Analysis engines return structured findings.

### Task 4.3: Object Fingerprinting

Status: complete

Validation Evidence:

- Stable fingerprints implemented for address objects/groups, service
  objects/groups, and tags.
- Tests cover equivalent address normalization and unsupported warnings.
- `pytest -q` passed with 65 tests.
- `ruff check .` passed.

Goal:

Create stable fingerprints for normalized address, address group, service,
service group, tag, and future object types.

Implementation Notes:

- Normalize comparable values before hashing or tuple comparison.
- Preserve object type and meaningful attributes.
- Keep scope separate from intrinsic object value.
- Warn for unsupported or incomplete normalized objects.

Validation:

- Tests cover equivalent fingerprints.
- Tests cover different fingerprints.
- Tests cover unsupported object warnings.
- `pytest` passes.
- `ruff check .` passes.

Completion Criteria:

- Duplicate detection can rely on stable object fingerprints.

### Task 4.4: Address Duplicate Detection

Status: complete

Validation Evidence:

- Address duplicate findings implemented for normalized address values and
  address groups.
- Tests cover duplicate address object detection and dynamic group warnings.
- `pytest -q` passed with 65 tests.
- `ruff check .` passed.

Goal:

Detect address objects and address groups with identical or equivalent values.

Implementation Notes:

- Support `ip-netmask`, `ip-range`, FQDN, and static address groups.
- Preserve dynamic address groups as warnings unless deterministic comparison is
  implemented.
- Compare within and across scopes while preserving scope context.

Validation:

- Tests cover exact address duplicates.
- Tests cover address group duplicates.
- Tests cover dynamic group warning behavior.
- `pytest` passes.
- `ruff check .` passes.

Completion Criteria:

- Address duplicate findings are deterministic and scope-aware.

### Task 4.5: Service Duplicate Detection

Status: complete

Validation Evidence:

- Service object/group fingerprinting and duplicate analysis implemented.
- Tests cover unsupported service port syntax warnings.
- `pytest -q` passed with 65 tests.
- `ruff check .` passed.

Goal:

Detect service objects and service groups with identical protocol/port
definitions.

Implementation Notes:

- Normalize TCP/UDP destination and source port specs.
- Compare service groups by normalized member fingerprints where practical.
- Warn for unsupported syntax.

Validation:

- Tests cover exact service duplicates.
- Tests cover service group duplicates.
- Tests cover non-duplicates.
- `pytest` passes.
- `ruff check .` passes.

Completion Criteria:

- Service duplicate findings explain matching protocol/port values.

### Task 4.6: Same-Name Conflict Detection

Status: complete

Validation Evidence:

- Same-name/different-value conflict findings implemented across scopes.
- Tests cover Panorama-style same-name conflict context.
- `pytest -q` passed with 65 tests.
- `ruff check .` passed.

Goal:

Detect same-name objects with different values across scopes where inheritance
or override behavior may matter.

Implementation Notes:

- Compare objects with the same name and type across Shared, Device Group, and
  vsys scopes.
- Distinguish intentional overrides from ambiguous conflicts where metadata
  permits.
- Do not claim runtime override safety until validated.

Validation:

- Tests cover same-name/different-value conflicts.
- Tests cover same-name/same-value duplicates.
- Tests cover Panorama scope context.
- `pytest` passes.
- `ruff check .` passes.

Completion Criteria:

- Conflict findings preserve scope and value differences.

### Task 4.7: Unused Object Candidate Detection

Status: complete

Validation Evidence:

- Unused candidate findings implemented from parsed reference/dependency
  records.
- Tests cover referenced and unreferenced objects plus parser coverage warnings.
- `pytest -q` passed with 65 tests.
- `ruff check .` passed.

Goal:

Identify objects that appear unreferenced by parsed rules and object groups.

Implementation Notes:

- Use Phase 1 references/dependencies where practical.
- Include warning that unparsed config sections may still reference objects.
- Distinguish unreferenced by parsed security policy from globally unused.

Validation:

- Tests cover referenced and unreferenced objects.
- Tests cover warnings for limited parser coverage.
- `pytest` passes.
- `ruff check .` passes.

Completion Criteria:

- Unused findings are clearly labeled as candidates.

### Task 4.8: Scope Placement Recommendations

Status: complete

Validation Evidence:

- Advisory placement recommendations implemented for duplicate values in
  multiple non-shared scopes.
- Tests cover shared-placement review candidates.
- `pytest -q` passed with 65 tests.
- `ruff check .` passed.

Goal:

Suggest review candidates for moving duplicate objects to Shared or more
specific scopes without staging changes.

Implementation Notes:

- Recommend only when supporting evidence is deterministic.
- Preserve warnings for Device Group inheritance and override uncertainty.
- Keep recommendations separate from Modify/Migrate plans.

Validation:

- Tests cover safe recommendation candidates.
- Tests cover no-recommendation cases.
- `pytest` passes.
- `ruff check .` passes.

Completion Criteria:

- Recommendations are advisory and never mutate plans.

### Task 4.9: CLI Dedupe/Conflict Command

Status: complete

Validation Evidence:

- `frying-pan dedupe-analysis` added with text, JSON, and Markdown report
  output.
- CLI worked against Panorama and firewall fixtures.
- `tests/test_cli_inventory.py` covers JSON and Markdown output.
- `pytest -q` passed with 65 tests.
- `ruff check .` passed.

Goal:

Expose dedupe and conflict analysis through the CLI.

Implementation Notes:

- Add command such as `frying-pan dedupe-analysis path/to/config.xml`.
- Support optional scope/type filters.
- Support text summary and JSON output.
- Support Markdown report output if practical.

Validation:

- CLI works against Panorama fixture.
- CLI works against firewall fixture.
- JSON output includes finding details.
- `pytest` passes.
- `ruff check .` passes.

Completion Criteria:

- CLI uses the same core analysis engine as GUI and tests.

### Task 4.10: GUI Dedupe And Conflict Display

Status: complete

Validation Evidence:

- Dedupe/Conflict GUI page added with summary, findings table, and detail view.
- `tests/test_gui_dedupe.py` passed offscreen.
- `pytest -q` passed with 65 tests.
- `ruff check .` passed.

Goal:

Display dedupe/conflict findings in the PySide6 GUI without embedding analysis
logic in GUI classes.

Implementation Notes:

- Provide table filters for type, severity, scope, and object type.
- Provide detail panel for selected finding.
- Label findings as advisory.

Validation:

- Offscreen GUI construction test passes.
- GUI tests cover result population where practical.
- `pytest` passes.
- `ruff check .` passes.

Completion Criteria:

- GUI can display core analysis results.

### Task 4.11: Dedupe/Conflict Report Export

Status: complete

Validation Evidence:

- JSON serialization available through Pydantic result models.
- Markdown export added in `frying_pan/export/dedupe_report_exporter.py`.
- `tests/test_dedupe_report_exporter.py` passed.
- `pytest -q` passed with 65 tests.
- `ruff check .` passed.

Goal:

Export dedupe and conflict findings for local review.

Implementation Notes:

- Support JSON serialization.
- Support Markdown report export if practical.
- Include source summary, finding counts, findings, warnings, and limitations.
- Do not imply automatic cleanup or XML mutation.

Validation:

- Tests verify serialization.
- Tests verify Markdown output if implemented.
- `pytest` passes.
- `ruff check .` passes.

Completion Criteria:

- Reports are local, review-oriented, and honest about limitations.

### Task 4.12: Final Phase 4 Validation

Status: complete

Validation Evidence:

- `pytest -q` passed with 65 tests.
- `ruff check .` passed.
- Existing CLI commands still worked against fixtures during regression
  validation.
- `frying-pan dedupe-analysis` worked against Panorama and firewall fixtures.
- Dedupe/conflict GUI/model and report export tests passed.
- `docs/dedupe-conflict-notes.md` and roadmap references were updated.
- No XML mutation/export support was enabled.

Goal:

Confirm Phase 4 is complete, tested, documented, and consistent with
architecture guardrails.

Validation:

- `pytest` passes.
- `ruff check .` passes.
- Existing CLI commands still work against fixtures.
- New dedupe/conflict CLI command works against Panorama and firewall fixtures.
- Offscreen GUI construction passes.
- Dedupe/conflict GUI/model tests pass.
- Report export tests pass if export is implemented.
- `docs/dedupe-conflict-notes.md` is updated.
- No XML mutation/export is enabled.

Completion Criteria:

- Every Phase 4 Task is complete.
- Full Phase 4 validation suite passes.
- Validation evidence is recorded.

## Phase 4 Completion Rules

A task cannot be marked complete unless its validation criteria are satisfied.

A phase cannot be marked complete unless all tasks are complete and the full
validation suite passes.

## Architecture Guardrails

- Keep analysis logic in GUI-independent core modules.
- Use normalized models and dependency records as inputs.
- Treat recommendations as advisory until Modify/Migrate phases stage them.
- Do not mutate source XML.
- Emit warnings for unparsed sections and inheritance uncertainty.
