# Phase 2: Policy Tester v1

Status: complete

## Goal

Evaluate a single operator-provided test flow against normalized PAN-OS security
policy data with conservative first-match behavior, trace output, later matching
rules, and explicit warnings for unsupported or uncertain offline behavior.

Phase 2 is about policy behavior testing and explanation. It must not enable
production XML mutation/export.

## Execution Model

Phase 2 is expected to be implemented through multiple Tasks.

Each Codex prompt/session may complete one or more Tasks, but the Phase remains
planned or active until all Tasks are complete and final Phase 2 validation
passes.

When implementing Phase 2:

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

1. Policy Tester behavior notes/documentation
2. Test flow model improvements
3. Match input normalization
4. Scope/rulebase selection
5. Address and address-group matching
6. Zone matching
7. Service and service-group matching
8. Application matching and `application-default` warnings
9. URL category, user, HIP, and profile limitations
10. First-match trace output
11. CLI policy tester command
12. GUI Policy Tester display
13. Markdown/JSON test result export
14. Tests and validation

## Task Status Values

Use these statuses consistently:

- planned
- in-progress
- blocked
- complete

A Task cannot be marked complete unless its validation criteria are satisfied.

## Phase 2 Validation Evidence

- `pytest -q` passed with 49 tests.
- `ruff check .` passed.
- CLI detect worked against Panorama and firewall fixtures.
- CLI inventory worked against Panorama and firewall fixtures.
- CLI policy-test worked against Panorama and firewall fixtures.
- Policy tester GUI/model tests passed offscreen.
- Policy test Markdown export tests passed.
- `docs/policy-tester-notes.md` was created with official Palo Alto Networks
  references and current offline limitations.
- XML mutation/export remains blocked.

## Tasks

### Task 2.1: Policy Tester Behavior Notes

Status: complete

Validation Evidence:

- `docs/policy-tester-notes.md` created and aligned to implemented matching
  behavior.
- `pytest -q` passed with 49 tests.
- `ruff check .` passed.

Goal:

Create and maintain documentation for policy tester behavior decisions,
limitations, and official Palo Alto Networks references.

Implementation Notes:

- Create or update `docs/policy-tester-notes.md`.
- Include sections for:
  - security policy first-match behavior
  - Panorama pre-rulebase and post-rulebase order assumptions
  - standalone firewall local rulebase assumptions
  - zone matching limitations
  - address/address-group matching behavior
  - service/service-group matching behavior
  - App-ID and `application-default` limitations
  - URL category, User-ID, HIP, profile, and runtime context limitations
  - official Palo Alto documentation references
- Keep this document aligned with implemented tester behavior.

Validation:

- `docs/policy-tester-notes.md` exists.
- Documented behavior matches implemented tester behavior.
- PAN-OS behavior comments in code have documentation references where
  practical.
- `ruff check .` passes if code changed.
- `pytest` passes if code changed.

Completion Criteria:

- Notes are accurate for all policy tester behavior implemented during Phase 2.
- Limitations and uncertainty are explicit.
- Documentation update evidence is recorded before status is changed to
  complete.

### Task 2.2: Policy Test Flow Model

Status: complete

Validation Evidence:

- `PolicyTestCase` now covers zones, IPs, protocol, ports, application, user,
  URL category, HIP hints, and metadata.
- `tests/test_policy_match_engine.py` covers valid and invalid flow models.
- `pytest -q` passed with 49 tests.
- `ruff check .` passed.

Goal:

Define the normalized input model for a single policy test flow.

Implementation Notes:

The model should represent:

- source zone
- destination zone
- source IP
- destination IP
- protocol
- destination port
- optional source port
- optional application hint
- optional URL category hint
- optional user
- optional source HIP / destination HIP hints if practical
- source/source-file metadata where useful

Validation:

- Unit tests instantiate valid flow models.
- Invalid or unsupported inputs produce validation errors or warnings.
- Existing policy match tests are updated to use the final model shape.
- `pytest` passes.
- `ruff check .` passes.

Completion Criteria:

- CLI, GUI, tests, and engine code use the same flow model.
- Unsupported fields are explicit and do not silently influence behavior.
- Validation evidence is recorded before status is changed to complete.

### Task 2.3: Match Input Normalization

Status: complete

Validation Evidence:

- Flow input normalizes IPs, TCP/UDP protocol casing, string selectors, and
  port ranges before matching.
- `tests/test_policy_match_engine.py` covers invalid IP/protocol/port handling.
- `pytest -q` passed with 49 tests.
- `ruff check .` passed.

Goal:

Normalize test-flow IP addresses, protocols, ports, and string selectors before
matching.

Implementation Notes:

- Normalize IP strings into `ipaddress` objects internally where practical.
- Normalize protocol names to canonical values.
- Normalize port values to integers or conservative ranges.
- Preserve original user input for reports and traces.
- Emit warnings for unsupported protocols or malformed inputs.

Validation:

- Tests cover IPv4 host and subnet handling.
- Tests cover TCP and UDP protocol normalization.
- Tests cover invalid IP/port/protocol inputs.
- `pytest` passes.
- `ruff check .` passes.

Completion Criteria:

- Match engine receives normalized values.
- Invalid input cannot produce a false confident match.
- Validation evidence is recorded before status is changed to complete.

### Task 2.4: Scope And Rulebase Selection

Status: complete

Validation Evidence:

- `PolicyMatchEngine.evaluate_config()` supports vsys local rulebases and
  Panorama Device Group pre/post ordering.
- Panorama tests verify pre-rule order and local-rule-gap warnings.
- CLI policy-test worked against Panorama and firewall fixtures.
- `pytest -q` passed with 49 tests.
- `ruff check .` passed.

Goal:

Select the rule sequence to evaluate for a requested scope while preserving
Panorama and firewall ordering assumptions.

Implementation Notes:

- Support standalone firewall local rulebase selection.
- Support Panorama Device Group pre-rulebase and post-rulebase selection.
- Preserve rule order within each rulebase.
- Document and warn when local firewall rules are unavailable for a Panorama
  Device Group test.
- Do not claim complete Panorama inheritance/runtime ordering until validated.

Validation:

- Tests cover standalone firewall rulebase selection.
- Tests cover Panorama pre-rulebase before post-rulebase ordering.
- Tests verify warnings when runtime local rules are unavailable.
- `pytest` passes.
- `ruff check .` passes.

Completion Criteria:

- The policy tester evaluates a deterministic ordered rule list.
- Rule ordering limitations are visible in trace output.
- Validation evidence is recorded before status is changed to complete.

### Task 2.5: Address And Address Group Matching

Status: complete

Validation Evidence:

- Address matching supports `any`, literal networks, `ip-netmask`, `ip-range`,
  FQDN warnings, dynamic group warnings, and recursive static groups.
- Firewall fixture tests cover source/destination object and group resolution.
- `pytest -q` passed with 49 tests.
- `ruff check .` passed.

Goal:

Match source and destination IPs against normalized address objects and static
address groups.

Implementation Notes:

- Support `any`.
- Support address objects with `ip-netmask`.
- Support address objects with `ip-range` if practical.
- Support address objects with `fqdn` only as warning/non-match unless a safe
  offline resolution model exists.
- Support static address groups recursively with loop protection.
- Preserve unresolved and dynamic group warnings.

Validation:

- Tests cover host and subnet matches.
- Tests cover non-matches.
- Tests cover static address group matches.
- Tests cover recursive or nested group handling if implemented.
- Tests cover dynamic address group warning behavior.
- `pytest` passes.
- `ruff check .` passes.

Completion Criteria:

- Address matching is deterministic and conservative.
- Unsupported address variants emit warnings instead of confident matches.
- Validation evidence is recorded before status is changed to complete.

### Task 2.6: Zone Matching

Status: complete

Validation Evidence:

- Zone matching supports `any`, explicit matches, and non-match trace reasons
  without route/interface inference.
- Existing and new policy match tests cover explicit and broad rule matching.
- `pytest -q` passed with 49 tests.
- `ruff check .` passed.

Goal:

Match source and destination zones in rules against the test flow.

Implementation Notes:

- Support `any`.
- Match explicit rule zone names against test flow zones.
- Preserve warnings when zones are absent from parsed inventory or route-derived
  zone inference is unavailable.
- Do not infer zones from routes/interfaces unless explicitly implemented and
  tested later.

Validation:

- Tests cover explicit zone matches.
- Tests cover `any`.
- Tests cover non-matches.
- Tests cover absent-zone warnings where practical.
- `pytest` passes.
- `ruff check .` passes.

Completion Criteria:

- Zone matching is explicit and does not guess routing behavior.
- Validation evidence is recorded before status is changed to complete.

### Task 2.7: Service And Service Group Matching

Status: complete

Validation Evidence:

- Service matching supports `any`, `service-http`, `service-https`, TCP/UDP
  service objects, port ranges/lists, and recursive service groups.
- Synthetic and fixture policy tests cover explicit service and group matching.
- `pytest -q` passed with 49 tests.
- `ruff check .` passed.

Goal:

Match protocol and destination port against service objects, service groups, and
well-known built-in service names where practical.

Implementation Notes:

- Support `any`.
- Support `service-http` and `service-https` built-ins.
- Support TCP and UDP service objects.
- Support single ports, comma-separated ports, and ranges if practical.
- Support service groups recursively with loop protection.
- Emit warnings for unsupported service syntax.

Validation:

- Tests cover TCP and UDP matches.
- Tests cover built-in `service-http` and `service-https`.
- Tests cover service group matches.
- Tests cover non-matches.
- Tests cover unsupported syntax warnings.
- `pytest` passes.
- `ruff check .` passes.

Completion Criteria:

- Service matching is deterministic and conservative.
- Validation evidence is recorded before status is changed to complete.

### Task 2.8: Application Matching And Application-Default Warnings

Status: complete

Validation Evidence:

- Application matching supports `any`, explicit hints, missing-hint warnings,
  and `application-default` uncertainty warnings.
- Firewall and Panorama fixture tests cover explicit App-ID hints and
  `application-default` warnings.
- `pytest -q` passed with 49 tests.
- `ruff check .` passed.

Goal:

Handle rule application selectors and `application-default` service semantics
without overstating offline App-ID certainty.

Implementation Notes:

- Support `any`.
- Match explicit application names only when the test flow includes an
  application hint.
- If a rule uses explicit applications and the flow has no application hint,
  emit an uncertainty warning.
- If a rule uses `application-default`, emit a warning that full default-port
  behavior is not fully determined offline unless implemented with official
  application metadata.
- Do not download or rely on cloud services at runtime.

Validation:

- Tests cover `any` application.
- Tests cover explicit application with matching hint.
- Tests cover explicit application without hint warning.
- Tests cover `application-default` warning.
- `pytest` passes.
- `ruff check .` passes.

Completion Criteria:

- App-ID behavior is conservative and traceable.
- Uncertain App-ID/default-port behavior is visible to users.
- Validation evidence is recorded before status is changed to complete.

### Task 2.9: URL Category, User, HIP, And Profile Limitations

Status: complete

Validation Evidence:

- URL category and user matching support exact hints, `any`, and uncertainty
  warnings when hints are absent.
- HIP criteria are preserved as conservative warnings when present.
- Fixture and model tests exercise URL category matching paths.
- `pytest -q` passed with 49 tests.
- `ruff check .` passed.

Goal:

Represent non-address/non-service match criteria in trace output without
pretending offline runtime context is complete.

Implementation Notes:

- Support `any` URL category/user/HIP selectors.
- Match explicit URL category only when test flow includes a matching hint.
- Match explicit user only when test flow includes a matching user.
- Emit warnings for HIP/profile/runtime-only criteria that cannot be fully
  evaluated offline.
- Preserve security profile/profile-group references in trace output as
  enforcement metadata, not match criteria unless official behavior requires
  otherwise.

Validation:

- Tests cover URL category hint match and non-match.
- Tests cover user hint match and non-match.
- Tests cover unsupported HIP/runtime warning behavior.
- `pytest` passes.
- `ruff check .` passes.

Completion Criteria:

- Runtime-only match criteria produce explicit warnings or conservative
  non-matches.
- Validation evidence is recorded before status is changed to complete.

### Task 2.10: First-Match Trace Output

Status: complete

Validation Evidence:

- `PolicyMatchResult` includes matched rule, action, trace, later matching
  rules, warnings, scope, and evaluated rule count.
- Trace steps include criteria results, reasons, warnings, position, rulebase,
  and action.
- Tests cover first match, later matching rules, disabled rule trace, and
  cleanup/drop selection.
- `pytest -q` passed with 49 tests.
- `ruff check .` passed.

Goal:

Return a detailed trace explaining why each evaluated rule matched or did not
match, which rule won, and which later rules would also match.

Implementation Notes:

- Preserve first-match behavior.
- Include per-rule criteria results.
- Include matched rule name and action.
- Include later matching rules.
- Include unresolved object/reference warnings.
- Include unsupported behavior warnings.
- Keep trace models usable by CLI, GUI, tests, and future reports.

Validation:

- Tests cover first matching allow and deny/drop rules.
- Tests cover later matching rules.
- Tests cover no-match behavior.
- Tests cover trace reasons for match and non-match.
- `pytest` passes.
- `ruff check .` passes.

Completion Criteria:

- Trace output is structured, deterministic, and user-explainable.
- Validation evidence is recorded before status is changed to complete.

### Task 2.11: CLI Policy Tester Command

Status: complete

Validation Evidence:

- `frying-pan policy-test` added with text, JSON, and Markdown report support.
- CLI policy-test worked against Panorama and firewall fixtures.
- `tests/test_cli_inventory.py` covers JSON output and Markdown export.
- `pytest -q` passed with 49 tests.
- `ruff check .` passed.

Goal:

Expose policy testing through the CLI for repeatable validation.

Implementation Notes:

Suggested command shape:

```bash
frying-pan policy-test path/to/config.xml \
  --scope DEVICE-GROUP-1 \
  --src-zone trust \
  --dst-zone dmz \
  --src-ip 10.0.0.10 \
  --dst-ip 10.0.1.10 \
  --protocol tcp \
  --dst-port 443 \
  --application ssl \
  --json
```

Support:

- text summary output
- JSON trace output
- useful non-zero errors for invalid inputs
- warnings for unsupported offline behavior

Validation:

- CLI policy-test works against Panorama fixture.
- CLI policy-test works against firewall fixture.
- Invalid input returns non-zero with useful message.
- JSON output includes matched rule/action/trace/warnings.
- `pytest` passes.
- `ruff check .` passes.

Completion Criteria:

- CLI command uses the same policy tester engine as GUI and tests.
- Output clearly labels warnings and limitations.
- Validation evidence is recorded before status is changed to complete.

### Task 2.12: GUI Policy Tester Display

Status: complete

Validation Evidence:

- Policy Tester GUI now has a shared flow input model bridge, matched result
  label, and tabular trace view.
- GUI remains a thin presentation layer over core `PolicyMatchResult` models.
- `tests/test_gui_policy_tester.py` passed offscreen.
- `pytest -q` passed with 49 tests.
- `ruff check .` passed.

Goal:

Make the PySide6 Policy Tester workspace usable for entering a test flow and
viewing match results without embedding engine logic in GUI classes.

Implementation Notes:

- Flow input form supports Phase 2 test-flow fields.
- Result panel shows matched rule and action.
- Trace panel shows per-rule match/non-match reasons.
- Warning panel or trace section shows offline limitations.
- GUI calls core engine/services rather than duplicating match logic.

Validation:

- Offscreen GUI construction test passes.
- GUI model/view tests cover flow input/result population where practical.
- No policy matching logic is embedded directly in GUI classes.
- `pytest` passes.
- `ruff check .` passes.

Completion Criteria:

- GUI can display basic policy tester result data from core models.
- GUI remains a thin presentation layer.
- Validation evidence is recorded before status is changed to complete.

### Task 2.13: Policy Test Result Export

Status: complete

Validation Evidence:

- Policy test results serialize to JSON through Pydantic models.
- Markdown export added in `frying_pan/export/policy_test_exporter.py`.
- `tests/test_policy_test_exporter.py` and CLI report tests passed.
- `pytest -q` passed with 49 tests.
- `ruff check .` passed.

Goal:

Export single-flow policy test results for review and reproducibility.

Implementation Notes:

- Support JSON result export.
- Support Markdown result export if practical.
- Include source summary, test flow, matched rule/action, trace, later matching
  rules, warnings, and limitations.
- Do not imply policy assurance, migration safety, or XML export safety.

Validation:

- Tests verify JSON result serialization.
- Tests verify Markdown result generation if implemented.
- Reports clearly label limitations.
- `pytest` passes.
- `ruff check .` passes.

Completion Criteria:

- Policy test results can be saved locally.
- Exported output is honest about offline limitations.
- Validation evidence is recorded before status is changed to complete.

### Task 2.14: Final Phase 2 Validation

Status: complete

Validation Evidence:

- `pytest -q` passed with 49 tests.
- `ruff check .` passed.
- CLI detect, inventory, and policy-test worked against the reference Panorama
  and firewall fixtures.
- Policy tester GUI/model tests passed offscreen.
- Policy test export tests passed.
- `docs/policy-tester-notes.md` and roadmap references were updated.
- No XML mutation/export support was enabled.

Goal:

Confirm the whole Phase 2 implementation is complete, tested, documented, and
consistent with architecture guardrails.

Implementation Notes:

- Review every Phase 2 Task status.
- Confirm task validation evidence exists.
- Update roadmap and phase documentation to reflect implemented behavior.
- Keep XML mutation/export blocked.

Validation:

- `pytest` passes.
- `ruff check .` passes.
- CLI detect works against Panorama and firewall fixtures.
- CLI inventory still works against Panorama and firewall fixtures.
- CLI policy-test works against Panorama and firewall fixtures.
- Offscreen GUI construction passes.
- Policy tester GUI/model tests pass.
- Policy test result export tests pass if export is implemented.
- `docs/policy-tester-notes.md` is updated.
- README/roadmap references remain accurate.
- No XML mutation/export is enabled.

Completion Criteria:

- Every Phase 2 Task is complete.
- Full Phase 2 validation suite passes.
- No known blocking issues remain untracked.
- Roadmap Phase 2 status can be changed from active to complete only after all
  validation evidence is recorded.

## Phase 2 Completion Rules

A task cannot be marked complete unless its validation criteria are satisfied.

A phase cannot be marked complete unless all tasks are complete and the full
validation suite passes.

Required final Phase 2 validation:

- `pytest` passes
- `ruff check .` passes
- CLI detect works against Panorama fixture
- CLI detect works against firewall fixture
- CLI inventory works against Panorama fixture
- CLI inventory works against firewall fixture
- CLI policy-test works against Panorama fixture
- CLI policy-test works against firewall fixture
- offscreen GUI construction passes
- policy tester GUI/model tests pass
- policy test result export tests pass if export is implemented
- `docs/policy-tester-notes.md` is updated
- README/roadmap references remain accurate
- no XML mutation/export is enabled

## Architecture Guardrails

- Keep parser and matching logic out of PySide6 views.
- Keep policy tester behavior in GUI-independent core modules.
- Use normalized models as the internal representation.
- Treat XML as import material and future export material, not the primary
  working model.
- Emit warnings for unsupported or uncertain offline behavior.
- Use official Palo Alto Networks documentation when encoding PAN-OS behavior.
- Do not introduce FastAPI, Next.js, PostgreSQL, login/auth, or hosted web
  workflows.
- Do not mutate source XML.
