# Phase 3: Policy Audit v1

Status: complete

## Goal

Analyze imported PAN-OS security rulebases for structured audit findings such
as obvious shadows, duplicate rules, broad allows, missing references, disabled
rules, logging gaps, App-ID/service uncertainty, and cleanup rule posture.

Phase 3 is about read-only policy analysis and reporting. It must not mutate
source XML or claim production-safe export.

## Execution Model

Phase 3 is expected to be implemented through multiple Tasks.

Each Codex prompt/session may complete one or more Tasks, but the Phase remains
planned or active until all Tasks are complete and final Phase 3 validation
passes.

When implementing Phase 3:

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

1. Policy Audit behavior notes/documentation
2. Audit finding model
3. Rulebase selection and scope handling
4. Missing and unresolved reference findings
5. Duplicate rule findings
6. Obvious full-shadow findings
7. Broad allow and cleanup rule findings
8. Disabled rule and logging findings
9. App-ID/service uncertainty findings
10. CLI policy audit command
11. GUI Policy Audit display
12. Markdown/JSON audit report export
13. Tests and validation

## Task Status Values

Use these statuses consistently:

- planned
- in-progress
- blocked
- complete

A Task cannot be marked complete unless its validation criteria are satisfied.

## Phase 3 Validation Evidence

- `pytest -q` passed with 57 tests.
- `ruff check .` passed.
- CLI detect, inventory, policy-test, and policy-audit worked against reference fixtures.
- Policy audit GUI/model tests passed offscreen.
- Policy audit Markdown export tests passed.
- `docs/policy-audit-notes.md` was created with official Palo Alto Networks references and current offline limitations.
- XML mutation/export remains blocked.

## Tasks

### Task 3.1: Policy Audit Behavior Notes

Status: complete

Validation Evidence:

- `docs/policy-audit-notes.md` created and aligned to implemented audit
  behavior.
- `pytest -q` passed with 57 tests.
- `ruff check .` passed.

Goal:

Document what Phase 3 policy audit checks mean, which checks are deterministic,
and which checks are conservative warnings.

Implementation Notes:

- Create or update `docs/policy-audit-notes.md`.
- Reference official Palo Alto Networks documentation where PAN-OS behavior is
  encoded.
- Document first-match dependency, Panorama pre/post ordering assumptions, and
  limitations inherited from Policy Tester.
- Document that audit findings are review signals, not automatic remediation.

Validation:

- Notes exist and match implemented checks.
- Code comments include official documentation URLs where practical.
- `pytest` passes if code changed.
- `ruff check .` passes if code changed.

Completion Criteria:

- Audit terminology and limitations are clear.
- Documentation update evidence is recorded before status is changed to
  complete.

### Task 3.2: Audit Finding Model

Status: complete

Validation Evidence:

- `AuditFinding` and `PolicyAuditResult` provide structured findings, computed
  counts, warnings, and JSON serialization.
- `tests/test_policy_audit_shadow.py` covers model serialization.
- `pytest -q` passed with 57 tests.
- `ruff check .` passed.

Goal:

Define structured policy audit finding models usable by core, CLI, GUI, tests,
and reports.

Implementation Notes:

- Include finding ID, severity, category, scope, rule names, affected criteria,
  explanation, warnings, and suggested operator review.
- Keep findings independent of GUI classes.
- Prefer explicit enums for severity and category.

Validation:

- Unit tests instantiate and serialize findings.
- JSON output is stable.
- `pytest` passes.
- `ruff check .` passes.

Completion Criteria:

- Policy audit engines return structured findings, not free-form strings only.

### Task 3.3: Rulebase Selection And Audit Context

Status: complete

Validation Evidence:

- `PolicyAuditEngine.audit_config()` supports scoped and whole-config audits.
- Firewall and Panorama fixture tests cover context selection and
  local-rule-gap warnings.
- `pytest -q` passed with 57 tests.
- `ruff check .` passed.

Goal:

Build a deterministic audit context for selected standalone firewall and
Panorama scopes.

Implementation Notes:

- Reuse Phase 2 scope and rulebase ordering where practical.
- Support whole-config audit and per-scope audit.
- Warn when Panorama local firewall rules are unavailable.
- Preserve scope metadata in findings.

Validation:

- Tests cover firewall vsys audit context.
- Tests cover Panorama Device Group context and local-rule-gap warning.
- `pytest` passes.
- `ruff check .` passes.

Completion Criteria:

- Audit checks operate on deterministic ordered rule sequences.

### Task 3.4: Missing And Unresolved Reference Findings

Status: complete

Validation Evidence:

- Unresolved references are converted into structured audit findings with
  selector type and target details.
- Tests cover unresolved source address references and fixture-derived
  unresolved references.
- `pytest -q` passed with 57 tests.
- `ruff check .` passed.

Goal:

Report security rules that reference unresolved objects, services, URL
categories, tags, users, or unsupported criteria.

Implementation Notes:

- Use Phase 1 references/dependencies where practical.
- Include rule name, selector, selector type, and scope in findings.
- Avoid guessing missing object intent.

Validation:

- Tests cover unresolved address/service references.
- Tests cover unresolved references in Panorama and firewall fixtures.
- `pytest` passes.
- `ruff check .` passes.

Completion Criteria:

- Missing references are visible in CLI, GUI, and reports.

### Task 3.5: Duplicate Rule Findings

Status: complete

Validation Evidence:

- Duplicate normalized criteria/action checks added.
- Tests cover duplicate rule findings.
- `pytest -q` passed with 57 tests.
- `ruff check .` passed.

Goal:

Detect rules with identical or materially equivalent normalized match criteria
and action.

Implementation Notes:

- Compare normalized source/destination zones, addresses, applications,
  services, users, URL categories, and action.
- Preserve order and scope context.
- Emit conservative warnings for unsupported criteria.

Validation:

- Tests cover exact duplicates.
- Tests cover same criteria with different action as separate risk category if
  implemented.
- Tests cover non-duplicates.
- `pytest` passes.
- `ruff check .` passes.

Completion Criteria:

- Duplicate findings are deterministic and explain the compared fields.

### Task 3.6: Obvious Full-Shadow Findings

Status: complete

Validation Evidence:

- Obvious supported-selector full-shadow checks added with a first-match
  documentation reference.
- Tests cover obvious full shadow behavior.
- `pytest -q` passed with 57 tests.
- `ruff check .` passed.

Goal:

Detect rules that can never be reached because an earlier rule clearly covers
all supported match criteria.

Implementation Notes:

- Start with deterministic full-shadow checks only.
- Treat unsupported criteria and object uncertainty as warnings.
- Do not claim partial shadow precision unless implemented and tested.
- Reuse Policy Tester matching primitives where practical.

Validation:

- Tests cover obvious `any` shadow behavior.
- Tests cover no-shadow behavior.
- Tests cover uncertainty warnings for App-ID/service limitations.
- `pytest` passes.
- `ruff check .` passes.

Completion Criteria:

- Full-shadow findings avoid false certainty.

### Task 3.7: Broad Allow And Cleanup Rule Findings

Status: complete

Validation Evidence:

- Broad allow, explicit cleanup, and missing cleanup advisory checks added.
- Tests and fixture CLI validation cover broad allow and cleanup findings.
- `pytest -q` passed with 57 tests.
- `ruff check .` passed.

Goal:

Identify broad allow rules and cleanup rule posture that warrant operator
review.

Implementation Notes:

- Detect broad `any`/`any`/`any` allow rules.
- Detect explicit cleanup rules and their action.
- Flag missing explicit cleanup only as advisory if default behavior is not
  synthesized.
- Include logging and profile context where parsed.

Validation:

- Tests cover broad allow findings.
- Tests cover explicit allow/deny/drop cleanup findings.
- Tests cover advisory no-cleanup behavior if implemented.
- `pytest` passes.
- `ruff check .` passes.

Completion Criteria:

- Findings are review-oriented and do not imply automatic remediation.

### Task 3.8: Disabled Rule And Logging Findings

Status: complete

Validation Evidence:

- Disabled rule and log-at-session-end review findings added.
- Firewall fixture tests cover disabled rule findings.
- `pytest -q` passed with 57 tests.
- `ruff check .` passed.

Goal:

Surface disabled rules and security rules missing expected logging posture.

Implementation Notes:

- Report disabled rules as informational/advisory.
- Report missing `log-end` or equivalent parsed logging settings where
  available.
- Preserve rule metadata from Phase 1 parsers.

Validation:

- Tests cover disabled rule findings.
- Tests cover logging findings from fixtures.
- `pytest` passes.
- `ruff check .` passes.

Completion Criteria:

- Disabled/logging findings include rule and scope context.

### Task 3.9: App-ID And Service Uncertainty Findings

Status: complete

Validation Evidence:

- App-ID/service review checks added for `application-default`, service-any
  with explicit applications, and port-based allows.
- Fixture tests cover `application-default` review findings.
- `pytest -q` passed with 57 tests.
- `ruff check .` passed.

Goal:

Identify rules where application/service combinations deserve review because
offline behavior cannot be fully determined.

Implementation Notes:

- Flag explicit applications paired with `any` service where useful.
- Flag service-only allows with application `any` where useful.
- Flag `application-default` as App-ID dependent rather than wrong.
- Reference official application-default documentation in comments where
  behavior is encoded.

Validation:

- Tests cover App-ID/service review findings.
- Tests cover `application-default` warning behavior.
- `pytest` passes.
- `ruff check .` passes.

Completion Criteria:

- Findings are conservative and explain runtime uncertainty.

### Task 3.10: CLI Policy Audit Command

Status: complete

Validation Evidence:

- `frying-pan policy-audit` added with text, JSON, scope selection, and
  Markdown report output.
- CLI policy-audit worked against Panorama and firewall fixtures.
- `tests/test_cli_inventory.py` covers JSON and Markdown output.
- `pytest -q` passed with 57 tests.
- `ruff check .` passed.

Goal:

Expose policy audit through the CLI for repeatable validation.

Implementation Notes:

- Add command such as `frying-pan policy-audit path/to/config.xml`.
- Support optional `--scope`.
- Support text summary and JSON output.
- Support Markdown report output if practical.

Validation:

- CLI policy-audit works against Panorama fixture.
- CLI policy-audit works against firewall fixture.
- JSON output includes finding count and finding details.
- `pytest` passes.
- `ruff check .` passes.

Completion Criteria:

- CLI uses the same core audit engine as GUI and tests.

### Task 3.11: GUI Policy Audit Display

Status: complete

Validation Evidence:

- Policy Audit GUI now displays summary, findings table, and finding detail
  from core models.
- `tests/test_gui_policy_audit.py` passed offscreen.
- `pytest -q` passed with 57 tests.
- `ruff check .` passed.

Goal:

Display policy audit findings in the PySide6 GUI without embedding audit logic
in GUI classes.

Implementation Notes:

- Provide findings table with severity/category/rule/scope.
- Provide detail panel for selected finding.
- Surface warnings and limitations.
- Keep GUI classes as presentation only.

Validation:

- Offscreen GUI construction test passes.
- GUI tests cover finding table/detail population where practical.
- `pytest` passes.
- `ruff check .` passes.

Completion Criteria:

- GUI can display audit results from core models.

### Task 3.12: Policy Audit Report Export

Status: complete

Validation Evidence:

- Policy audit results serialize to JSON through Pydantic models.
- Markdown export added in `frying_pan/export/policy_audit_exporter.py`.
- `tests/test_policy_audit_exporter.py` passed.
- `pytest -q` passed with 57 tests.
- `ruff check .` passed.

Goal:

Export policy audit results for local review.

Implementation Notes:

- Support JSON serialization.
- Support Markdown report export.
- Include source/scope summary, finding counts, findings, warnings, and
  limitations.
- Do not imply automated remediation or XML mutation.

Validation:

- Tests verify JSON serialization.
- Tests verify Markdown report generation if implemented.
- Reports clearly label limitations.
- `pytest` passes.
- `ruff check .` passes.

Completion Criteria:

- Audit results can be saved locally with honest limitations.

### Task 3.13: Final Phase 3 Validation

Status: complete

Validation Evidence:

- `pytest -q` passed with 57 tests.
- `ruff check .` passed.
- CLI detect, inventory, policy-test, and policy-audit worked against reference
  fixtures.
- Policy audit GUI/model and report export tests passed.
- `docs/policy-audit-notes.md` and roadmap references were updated.
- No XML mutation/export support was enabled.

Goal:

Confirm Phase 3 is complete, tested, documented, and consistent with
architecture guardrails.

Validation:

- `pytest` passes.
- `ruff check .` passes.
- CLI detect/inventory/policy-test still works against fixtures.
- CLI policy-audit works against Panorama and firewall fixtures.
- Offscreen GUI construction passes.
- Policy audit GUI/model tests pass.
- Audit report export tests pass if export is implemented.
- `docs/policy-audit-notes.md` is updated.
- No XML mutation/export is enabled.

Completion Criteria:

- Every Phase 3 Task is complete.
- Full Phase 3 validation suite passes.
- Validation evidence is recorded.

## Phase 3 Completion Rules

A task cannot be marked complete unless its validation criteria are satisfied.

A phase cannot be marked complete unless all tasks are complete and the full
validation suite passes.

## Architecture Guardrails

- Keep audit logic in GUI-independent core modules.
- Use normalized models as the internal representation.
- Treat audit findings as review signals, not automatic fixes.
- Emit warnings for unsupported or uncertain offline behavior.
- Do not mutate source XML.
- Use official Palo Alto Networks documentation when encoding PAN-OS behavior.
