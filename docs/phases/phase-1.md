# Phase 1: PAN-OS Inventory Analyzer

Status: active

## Goal

Import a Panorama or standalone Palo Alto firewall XML file, detect what it is,
parse common PAN-OS objects/rules into normalized entities, extract
references/dependencies, expose the inventory through CLI, and surface basic
inventory results in the GUI.

Phase 1 is about inventory and reporting. It must not enable production XML
mutation/export.

## Execution Model

Phase 1 is expected to be implemented through multiple Tasks.

Each Codex prompt/session may complete one or more Tasks, but the Phase remains
active until all Tasks are complete and final Phase 1 validation passes.

When implementing Phase 1:

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

1. Source detection improvements
2. PAN-OS XML notes/documentation
3. Panorama parser implementation
4. Standalone firewall parser implementation
5. Normalized inventory models
6. Object parsing
7. Security rule parsing
8. Reference extraction
9. Dependency map foundation
10. CLI inventory output
11. GUI inventory display
12. Markdown/HTML report foundation
13. Tests and validation

## Task Status Values

Use these statuses consistently:

- planned
- in-progress
- blocked
- complete

A Task cannot be marked complete unless its validation criteria are satisfied.

## Tasks

### Task 1.1: Source Detection Improvements

Status: planned

Goal:

Detect the main Phase 1 source types and structural capabilities before parser
selection.

Implementation Notes:

- Detect Panorama XML.
- Detect standalone firewall XML.
- Detect unknown PAN-OS XML.
- Detect PAN-OS version if available.
- Detect whether `shared` scope exists.
- Detect whether Device Groups exist.
- Detect whether `vsys` exists.
- Preserve warnings for ambiguous or unsupported inputs.
- Add or expand fixture coverage for Panorama, standalone firewall, unknown
  PAN-OS XML, and invalid XML.

Validation:

- `pytest` detection tests pass.
- CLI detection command works against a Panorama fixture.
- CLI detection command works against a firewall fixture.
- Invalid XML detection returns a useful warning/result.
- `ruff check .` passes.

Completion Criteria:

- Detection result models include the required structural fields.
- Tests cover each detection path.
- CLI output includes source type, PAN-OS version when present, and structural
  flags.
- Validation evidence is recorded before status is changed to complete.

### Task 1.2: PAN-OS XML Notes

Status: planned

Goal:

Create and maintain parser-relevant PAN-OS XML documentation as implementation
decisions are made.

Implementation Notes:

- Create or update `docs/panos-xml-notes.md`.
- Include sections for:
  - Panorama shared object paths
  - Panorama Device Group object paths
  - Panorama pre-rulebase paths
  - Panorama post-rulebase paths
  - standalone firewall/vsys object paths
  - standalone firewall/vsys rulebase paths
  - known parser limitations
  - official Palo Alto documentation references
  - implementation notes and uncertainties
- Keep this document aligned with implemented parser behavior.
- Add official documentation URLs where practical.

Validation:

- `docs/panos-xml-notes.md` exists.
- Documented paths match implemented parser behavior.
- Palo Alto-specific behavior comments in code have documentation references
  where practical.
- `ruff check .` passes if code changed.
- `pytest` passes if code changed.

Completion Criteria:

- Notes are accurate for all parser behavior implemented during Phase 1.
- Limitations and uncertainties are explicit.
- Documentation update evidence is recorded before status is changed to
  complete.

### Task 1.3: Panorama Parser Implementation

Status: planned

Goal:

Parse common Panorama XML inventory into normalized scopes, objects, tags, and
security rules.

Implementation Notes:

- Parse shared address objects.
- Parse shared address groups.
- Parse shared service objects.
- Parse shared service groups.
- Parse shared tags.
- Parse Device Group address objects.
- Parse Device Group address groups.
- Parse Device Group service objects.
- Parse Device Group service groups.
- Parse Device Group tags.
- Parse security pre-rules.
- Parse security post-rules.
- Do not crash on missing optional XML sections.
- Keep XML parsing isolated in source adapters and PAN-OS normalizer modules.

Validation:

- Tests cover at least one shared object fixture.
- Tests cover at least one Device Group object fixture.
- Tests cover at least one pre-rulebase security rule.
- Tests cover at least one post-rulebase security rule, if fixture exists.
- Parser does not crash on missing optional XML sections.
- `pytest` passes.
- `ruff check .` passes.

Completion Criteria:

- Panorama XML fixtures produce normalized `ConfigScope` and entity records.
- Parser warnings are emitted for unsupported sections or variants.
- Tests and docs reflect the implemented XML paths.
- Validation evidence is recorded before status is changed to complete.

### Task 1.4: Standalone Firewall Parser Implementation

Status: planned

Goal:

Parse common standalone PAN-OS firewall XML inventory without assuming
Panorama Device Group structure.

Implementation Notes:

- Parse `vsys`/local address objects.
- Parse `vsys`/local address groups.
- Parse `vsys`/local service objects.
- Parse `vsys`/local service groups.
- Parse `vsys`/local tags.
- Parse local security rules.
- Represent each `vsys` as a normalized scope.
- Keep firewall parser behavior separate from Panorama parser behavior.

Validation:

- Tests cover at least one standalone firewall fixture.
- Parser identifies `vsys`/local scope correctly.
- Parser does not assume Panorama Device Group structure.
- Parser does not crash on missing optional XML sections.
- `pytest` passes.
- `ruff check .` passes.

Completion Criteria:

- Firewall XML fixtures produce normalized scopes and entities.
- Standalone firewall limitations are documented.
- Validation evidence is recorded before status is changed to complete.

### Task 1.5: Normalized Inventory Models

Status: planned

Goal:

Ensure normalized models can represent the Phase 1 inventory and dependency
surface for Panorama and standalone firewall sources.

Implementation Notes:

Models must represent:

- `SourceConfig`
- `ConfigScope`
- `AddressObject`
- `AddressGroup`
- `ServiceObject`
- `ServiceGroup`
- `Tag`
- `SecurityRule`
- `Rulebase`
- `Reference`
- `Dependency`

Normalized entities should preserve:

- source file identity
- source type
- scope type
- scope name
- object/rule name
- object/rule type
- raw XML path or XPath-like location where practical
- original XML element reference metadata where practical
- normalized value
- warnings/limitations

Validation:

- Unit tests instantiate normalized models.
- Parsed Panorama objects produce normalized entities.
- Parsed firewall objects produce normalized entities.
- `pytest` passes.
- `ruff check .` passes.

Completion Criteria:

- Models can support all implemented parser output without ad hoc dictionaries
  as the primary internal representation.
- Tests prove both Panorama and firewall parsed data can use the models.
- Validation evidence is recorded before status is changed to complete.

### Task 1.6: Object Parsing

Status: planned

Goal:

Parse common PAN-OS object types into normalized object models.

Implementation Notes:

Address object support:

- `ip-netmask`
- `ip-range` if practical
- `fqdn` if practical
- description
- tags if present

Address group support:

- static members
- dynamic match expression placeholder/warning if not fully supported

Service object support:

- protocol `tcp`/`udp`
- destination port
- source port if present
- description
- tags if present

Service group support:

- static members

Tag support:

- name
- color if present
- comments if present

Validation:

- Tests cover each implemented object type.
- Unsupported object variants produce warnings instead of crashing.
- Object parser handles missing description/tags.
- `pytest` passes.
- `ruff check .` passes.

Completion Criteria:

- Implemented object types produce normalized entities with scope and source
  metadata.
- Unsupported or partial variants are clearly warned and documented.
- Validation evidence is recorded before status is changed to complete.

### Task 1.7: Security Rule Parsing

Status: planned

Goal:

Parse Phase 1 security rule inventory into normalized rule models while
preserving rulebase location and order.

Implementation Notes:

Parse security rules into normalized form with:

- rule name
- rulebase location
- rule order
- source zones
- destination zones
- source addresses
- destination addresses
- users if present
- applications
- services
- URL categories if present
- action
- disabled state
- tags
- description
- log settings if practical
- profile/profile-group references if practical
- raw location metadata

Validation:

- Tests cover at least one allow rule.
- Tests cover at least one deny/drop rule if fixture exists.
- Tests cover disabled rule detection.
- Tests cover source/destination/application/service extraction.
- Rule order is preserved.
- `pytest` passes.
- `ruff check .` passes.

Completion Criteria:

- Parsed rules are available to inventory reports and later policy phases.
- Unsupported match criteria create warnings instead of silent assumptions.
- Validation evidence is recorded before status is changed to complete.

### Task 1.8: Reference Extraction

Status: planned

Goal:

Extract structured references from parsed objects and rules so dependency
analysis can begin.

Implementation Notes:

Extract references from rules to:

- source address objects/groups
- destination address objects/groups
- service objects/groups
- applications
- zones
- tags
- profile groups/profiles if parsed
- URL categories if parsed

References should be structured records, not plain strings.

Validation:

- Tests verify references are extracted from a sample rule.
- Missing references produce warnings or unresolved reference records.
- `pytest` passes.
- `ruff check .` passes.

Completion Criteria:

- References include owner, target, reference kind, scope context, and resolved
  or unresolved status where practical.
- Limitations are documented.
- Validation evidence is recorded before status is changed to complete.

### Task 1.9: Dependency Map Foundation

Status: planned

Goal:

Build the first dependency map structure from parsed references.

Implementation Notes:

Represent at least:

- object -> referenced by rule
- object -> referenced by group
- service -> referenced by rule
- service -> referenced by group
- tag -> referenced by object/rule where practical

This does not need to be a complete graph engine yet, but it must establish the
data structure and tests.

Validation:

- Tests verify dependency records are created.
- Tests verify a rule depending on an address object is represented.
- Tests verify a group depending on member objects is represented.
- Missing or unresolved references do not crash dependency generation.
- `pytest` passes.
- `ruff check .` passes.

Completion Criteria:

- Dependency records are usable by reports and future audit/dedupe/migration
  phases.
- Deferred graph features are explicitly documented.
- Validation evidence is recorded before status is changed to complete.

### Task 1.10: CLI Inventory Output

Status: planned

Goal:

Expose inventory parsing through CLI commands for repeatable testing and
operator-friendly summaries.

Implementation Notes:

Support:

- detecting source type
- parsing inventory
- printing inventory summary
- optionally exporting inventory summary to JSON
- optionally exporting inventory report to Markdown

Suggested commands:

```bash
frying-pan detect path/to/config.xml
frying-pan inventory path/to/config.xml
frying-pan inventory path/to/config.xml --json
frying-pan inventory path/to/config.xml --report-md report.md
```

Validation:

- CLI detect works against Panorama fixture.
- CLI inventory works against Panorama fixture.
- CLI inventory works against firewall fixture if available.
- CLI returns non-zero and useful message for invalid XML.
- `pytest` passes.
- `ruff check .` passes.

Completion Criteria:

- CLI commands use the same parser/engine modules as the GUI and tests.
- Output does not imply modification, migration, or XML export safety.
- Validation evidence is recorded before status is changed to complete.

### Task 1.11: GUI Inventory Display

Status: planned

Goal:

Surface basic inventory visibility in the PySide6 GUI without embedding parser
logic in GUI classes.

Implementation Notes:

- Sources page can show imported source metadata.
- Inventory page/view can show counts by entity type.
- Inventory page/view can show scopes.
- Inventory page/view can show a basic object/rule table.
- GUI should call core parser/workspace services rather than duplicating parser
  logic.

Validation:

- Offscreen GUI construction test passes.
- GUI inventory model/view tests are added where practical.
- No parser logic is embedded directly in GUI classes.
- `pytest` passes.
- `ruff check .` passes.

Completion Criteria:

- GUI displays basic source/inventory data from core models.
- GUI remains a thin presentation layer.
- Validation evidence is recorded before status is changed to complete.

### Task 1.12: Markdown/HTML Report Foundation

Status: planned

Goal:

Generate clear inventory reports from parsed normalized data.

Implementation Notes:

Initial report should include:

- source file summary
- source type
- detected PAN-OS version if available
- scopes
- object counts
- rule counts
- unresolved reference counts
- parser warnings
- known limitations

Markdown is required for Phase 1. HTML is optional if it can be added without
over-scoping the task.

Validation:

- Test verifies Markdown report generation from parsed fixture.
- Report does not claim migration/modification safety.
- Report clearly labels limitations.
- `pytest` passes.
- `ruff check .` passes.

Completion Criteria:

- Inventory report can be produced from Phase 1 parser output.
- Reports are honest about limitations and blocked XML mutation/export.
- Validation evidence is recorded before status is changed to complete.

### Task 1.13: Final Phase 1 Validation

Status: planned

Goal:

Confirm the whole Phase 1 implementation is complete, tested, documented, and
consistent with architecture guardrails.

Implementation Notes:

- Review every Phase 1 Task status.
- Confirm task validation evidence exists.
- Update roadmap and phase documentation to reflect implemented behavior.
- Keep XML mutation/export blocked unless serializer tests exist.

Validation:

- `pytest` passes.
- `ruff check .` passes.
- CLI detect works against Panorama fixture.
- CLI inventory works against Panorama fixture.
- CLI detect works against firewall fixture if fixture exists.
- CLI inventory works against firewall fixture if fixture exists.
- Offscreen GUI construction passes.
- Inventory report generation test passes.
- `docs/panos-xml-notes.md` is updated.
- README/roadmap references remain accurate.
- No XML mutation/export is enabled unless serializer tests exist.

Completion Criteria:

- Every Phase 1 Task is complete.
- Full Phase 1 validation suite passes.
- No known blocking issues remain untracked.
- Roadmap Phase 1 status can be changed from active to complete only after all
  validation evidence is recorded.

## Phase 1 Completion Rules

A task cannot be marked complete unless its validation criteria are satisfied.

A phase cannot be marked complete unless all tasks are complete and the full
validation suite passes.

Required final Phase 1 validation:

- `pytest` passes
- `ruff check .` passes
- CLI detect works against Panorama fixture
- CLI inventory works against Panorama fixture
- CLI detect works against firewall fixture if fixture exists
- CLI inventory works against firewall fixture if fixture exists
- offscreen GUI construction passes
- inventory report generation test passes
- `docs/panos-xml-notes.md` is updated
- README/roadmap references remain accurate
- no XML mutation/export is enabled unless serializer tests exist

## Architecture Guardrails

- Keep parser logic out of PySide6 views.
- Keep source adapters responsible for source-specific parsing.
- Keep normalized models as the internal representation.
- Treat XML as import material and future export material, not the primary
  working model.
- Emit warnings for unsupported or uncertain variants.
- Use official Palo Alto Networks documentation when encoding PAN-OS behavior.
- Do not introduce FastAPI, Next.js, PostgreSQL, login/auth, or hosted web
  workflows.
