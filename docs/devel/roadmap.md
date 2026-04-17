# Frying-PAN Roadmap

This roadmap breaks implementation into practical phases that can be completed incrementally.

Each phase contains:

- a goal
- one or more tasks
- validation needed for a PASS mark

A phase should only be closed when every task in that phase has passed its validation criteria.

## Status Model

Use the following status values when this roadmap begins active tracking:

- `todo`
- `in_progress`
- `blocked`
- `pass`

## Phase 0: Foundation Reset

Goal:

- align the scaffold with the locked design decisions before deeper feature work begins

Status:

- `pass`

Tasks:

### 0.1 Convert backend baseline from SQLite-first to PostgreSQL-first

Status:

- `pass`

Work:

- update backend configuration defaults to PostgreSQL
- add SQLAlchemy/Alembic-friendly structure if missing
- remove SQLite-first assumptions from runtime configuration and docs where appropriate
- keep local storage paths for XML on disk

PASS validation:

- backend configuration defaults point to PostgreSQL
- no core docs contradict the PostgreSQL-first decision
- app starts with PostgreSQL settings without code edits

Suggested validation/tests:

- configuration review of env variables and settings
- backend startup test against a local PostgreSQL instance or container
- grep/review for stale SQLite-as-primary wording

### 0.2 Add migration framework baseline

Status:

- `pass`

Work:

- add Alembic configuration
- create initial migration layout
- confirm migrations can be generated and applied cleanly

PASS validation:

- Alembic is configured and runnable
- an empty or initial baseline migration can be applied successfully
- migration workflow is documented for contributors

Suggested validation/tests:

- run migration upgrade on a fresh database
- run migration downgrade/upgrade cycle on a scratch database

### 0.3 Define backend package boundaries for parser, persistence, and analysis

Status:

- `pass`

Work:

- make sure backend modules map cleanly to parser, persistence, analysis, merge planning, and export
- remove or mark any misleading placeholder code that implies unsupported behavior

PASS validation:

- module boundaries are reflected in code layout
- placeholder behavior is explicitly marked as placeholder
- no route handlers contain embedded config-semantic logic

Suggested validation/tests:

- code review against `AGENTS.md`
- import/syntax test for backend modules

## Phase 1: Project And Source Management

Goal:

- make projects and source XML imports real, persistent, and auditable

Status:

- `pass`

Tasks:

### 1.1 Implement PostgreSQL-backed project records

Status:

- `pass`

Work:

- create `projects` table and model
- support project create/list/detail flows
- persist project metadata in PostgreSQL

PASS validation:

- projects can be created and retrieved persistently
- project IDs remain stable across restarts
- project API responses match expected schema

Suggested validation/tests:

- API test for create/list/detail
- database verification of inserted project rows

### 1.2 Implement source import records and raw file storage

Status:

- `pass`

Work:

- create `sources` table and model
- store raw uploaded XML on disk
- create source rows with filename, checksum, storage path, and parse status

PASS validation:

- uploaded XML is written to disk
- source metadata is written to PostgreSQL
- duplicate upload handling is defined and behaves consistently

Suggested validation/tests:

- upload API test with a real XML file
- checksum verification test
- file existence check on storage path

### 1.3 Add project/source audit trail

Status:

- `pass`

Work:

- record meaningful events for project creation and source upload
- tie events to project scope

PASS validation:

- project create and source import actions generate auditable event records
- event history can be retrieved for a project

Suggested validation/tests:

- API or service test for event creation
- DB verification of expected event rows

## Phase 2: Scope Discovery And Canonical Inventory

Goal:

- parse imported XML into canonical scope and object inventory records

Status:

- `pass`

Tasks:

### 2.1 Parse scope hierarchy from Panorama XML

Status:

- `pass`

Work:

- parse `shared`
- parse device groups
- parse nested device groups
- capture parent-child relationships using Panorama metadata
- persist `scopes`

PASS validation:

- `Example-1.xml` produces expected scope records
- child DG parent linkage is captured correctly
- scope paths are stable and human-readable

Suggested validation/tests:

- parser unit test using `Example-1.xml`
- DB row count and content verification for discovered scopes

### 2.2 Parse v1 object types into canonical records

Status:

- `pass`

Work:

- parse address objects
- parse address groups
- parse services
- parse service groups
- parse tags
- persist `objects` using raw and normalized payloads

PASS validation:

- `Example-1.xml` produces the expected v1 object inventory
- object identity includes source, scope, object type, and name
- canonical payloads are stored without mutating source semantics

Suggested validation/tests:

- parser unit tests by object type
- fixture-based inventory comparison using `Example-1.xml`
- database verification of inserted object rows

### 2.3 Track parse warnings and unsupported object types cleanly

Status:

- `pass`

Work:

- record unsupported sections without crashing the import
- capture warnings for future work

PASS validation:

- unsupported sections do not abort the full import
- warnings are recorded in a queryable form
- imports can complete in a partial-but-honest state

Suggested validation/tests:

- import test with known unsupported content
- validation that warnings are persisted or returned consistently

## Phase 3: Reference Graph And Resolution

Goal:

- build the dependency graph needed for safe comparison and transformation

Status:

- `todo`

Tasks:

### 3.1 Extract outbound references from v1 object types

Work:

- parse group member references
- identify builtin references where applicable
- persist `references`

PASS validation:

- address-group and service-group references from `Example-1.xml` are captured
- builtin references are distinguished from imported object references

Suggested validation/tests:

- parser unit tests for `DG1-Group`, `Nested-Groups`, and `Shared-Service-Group`
- database verification of expected reference rows

### 3.2 Implement scope-aware reference resolution

Work:

- resolve in local DG first
- resolve through ancestor DG hierarchy
- resolve through `shared`
- resolve builtin namespaces
- mark unresolved and ambiguous references explicitly

PASS validation:

- local references resolve correctly
- ancestor/shared references resolve correctly
- unresolved references remain explicit

Suggested validation/tests:

- resolver unit tests using `Example-1.xml`
- targeted tests for local, ancestor, shared, builtin, and unresolved cases

### 3.3 Model precedence behavior as configuration, not parser magic

Work:

- define where precedence settings live
- ensure resolution logic can account for project/source precedence configuration

PASS validation:

- precedence behavior is externally configurable
- parser output does not hide precedence assumptions

Suggested validation/tests:

- resolver configuration tests
- review that precedence-sensitive behavior is isolated to resolution logic

## Phase 4: Analysis And Comparison

Goal:

- provide useful analysis outputs before any write-back or merge operations

Status:

- `todo`

Tasks:

### 4.1 Duplicate analysis by name and value

Work:

- implement duplicate-by-name analysis
- implement duplicate-by-normalized-value analysis
- support filtering by scope, source, and object type

PASS validation:

- duplicate reports identify expected objects in `Example-1.xml`
- analysis output clearly distinguishes same-name vs same-value findings

Suggested validation/tests:

- analysis tests for duplicate name findings
- analysis tests for duplicate normalized value findings
- API tests for filter behavior

### 4.2 Normalization suggestion analysis

Work:

- detect likely IPv4 host to `/32` suggestions
- detect likely IPv6 host to `/128` suggestions
- keep suggestions separate from applied changes

PASS validation:

- likely normalization candidates are surfaced
- no source data is silently rewritten during analysis

Suggested validation/tests:

- analysis test for `172.16.1.1` style suggestions
- regression test proving analysis does not mutate canonical stored values

### 4.3 Promotion candidate and blocker analysis

Work:

- identify objects that may be promotable to `shared`
- identify dependency blockers and collisions
- surface mixed-scope dependencies

PASS validation:

- candidate report includes both promotable items and blockers
- dependency-related blockers are visible and explainable

Suggested validation/tests:

- analysis tests for mixed-scope dependency chains
- API tests for promotion candidate reporting

## Phase 5: Change Sets And Transformation Preview

Goal:

- let users stage backend-planned changes without applying them blindly

Status:

- `todo`

Tasks:

### 5.1 Implement `change_sets` persistence and status flow

Work:

- create `change_sets` table and model
- support draft/preview/apply lifecycle states

PASS validation:

- change sets can be created and retrieved
- state transitions are explicit and validated

Suggested validation/tests:

- API/service tests for create/read/status transition
- DB verification of lifecycle state changes

### 5.2 Build promote-to-shared preview planning

Work:

- given selected objects, compute required object moves/promotions
- compute reference rewrites needed to keep the result valid
- record blockers instead of forcing unsafe plans

PASS validation:

- preview output includes planned object actions and reference rewrites
- unsafe plans are blocked with explicit reasons

Suggested validation/tests:

- planner unit tests on sample object graphs
- integration test using `Example-1.xml`-derived records

### 5.3 Add user-approved normalization changes to change-set planning

Work:

- allow user-selected normalization suggestions to become planned changes
- keep change preview explicit and reviewable

PASS validation:

- normalization changes only appear after explicit user selection
- preview distinguishes normalization from promotion/rewrite actions

Suggested validation/tests:

- planner tests for selected vs unselected suggestions
- API tests for change-set preview payload

## Phase 6: Apply Engine

Goal:

- safely apply reviewed changes to working project state

Status:

- `todo`

Tasks:

### 6.1 Define working-state mutation model

Work:

- decide how imported state and applied working state coexist
- ensure imported source data remains traceable and effectively immutable

PASS validation:

- applied changes do not destroy source provenance
- working-state model is documented and testable

Suggested validation/tests:

- architecture review against design doc
- service tests for immutable source preservation

### 6.2 Apply promote-to-shared and reference rewrite operations transactionally

Work:

- execute planned operations in a transaction
- update working objects and references consistently
- fail safely on invalid apply attempts

PASS validation:

- apply succeeds atomically for valid plans
- failed apply attempts leave state unchanged
- rewritten references are internally consistent after apply

Suggested validation/tests:

- transactional integration tests
- rollback tests with intentionally invalid operations
- post-apply graph consistency checks

## Phase 7: Export

Goal:

- generate XML output from transformed canonical state

Status:

- `todo`

Tasks:

### 7.1 Define export model and serialization boundary

Work:

- define how canonical state maps back to XML structures
- define how builtin and untouched imported elements are handled

PASS validation:

- export strategy is explicit and documented
- serialization boundaries do not depend on ad hoc text replacement

Suggested validation/tests:

- design review against locked export direction
- serializer unit tests for v1 object types

### 7.2 Generate v1 export for supported object types

Work:

- serialize supported v1 object types from canonical/project working state
- produce export file records and storage entries

PASS validation:

- exported XML is well-formed
- exported v1 objects reflect applied project state
- export artifacts are stored and traceable to a project/change set

Suggested validation/tests:

- XML well-formedness validation
- fixture comparison tests for serialized output
- export record and file existence checks

## Phase 8: Frontend Workbench Integration

Goal:

- expose project, import, analysis, and change workflows in the web UI

Status:

- `todo`

Tasks:

### 8.1 Project and source management UI

Work:

- project creation/list/detail views
- source upload UI
- source inventory visibility

PASS validation:

- users can create a project and upload XML from the UI
- UI reflects backend truth for project and source state

Suggested validation/tests:

- frontend integration tests
- manual end-to-end smoke test through the browser

### 8.2 Analysis and comparison UI

Work:

- duplicate views
- normalization suggestion views
- promotion candidate/blocker views

PASS validation:

- users can inspect analysis results without hidden backend assumptions
- filters and comparison output are understandable and consistent

Suggested validation/tests:

- UI integration tests for filters and result rendering
- manual validation against `Example-1.xml` findings

### 8.3 Change preview and apply UI

Work:

- change-set creation and review screens
- preview of planned rewrites
- apply flow and status feedback

PASS validation:

- users can review changes before apply
- apply status and failure reasons are visible in the UI

Suggested validation/tests:

- UI integration tests for preview/apply flow
- manual end-to-end test against a sample project

## Phase 9: Multi-User App Layer

Goal:

- add application-level identity and access control without polluting workbench semantics

Status:

- `todo`

Tasks:

### 9.1 Users, organizations, and memberships

Work:

- implement `users`
- implement `organizations`
- implement organization and project memberships

PASS validation:

- user and membership records persist correctly
- project access can be restricted by membership

Suggested validation/tests:

- backend tests for membership rules
- authorization tests for project access boundaries

### 9.2 Authentication and session flow

Work:

- add chosen auth/session approach
- keep auth concerns in the app layer only

PASS validation:

- authenticated access works for protected project routes
- unauthenticated or unauthorized access is rejected correctly

Suggested validation/tests:

- auth integration tests
- session lifecycle tests

### 9.3 Audit expansion for multi-user changes

Work:

- record actor-aware events for analysis, change-set creation, and apply/export actions

PASS validation:

- significant actions can be attributed to a user
- audit history is queryable per project

Suggested validation/tests:

- audit trail tests for user-attributed actions

## Phase 10: Hardening And Scale Validation

Goal:

- prove the system remains honest and usable as volume and complexity grow

Status:

- `todo`

Tasks:

### 10.1 Performance and indexing review

Work:

- review query patterns
- add or refine indexes
- validate import and analysis performance at meaningful scale

PASS validation:

- representative imports and analyses complete within acceptable thresholds
- index choices are justified by observed query behavior

Suggested validation/tests:

- import timing benchmarks
- analysis timing benchmarks
- query plan review for critical filters and lookups

### 10.2 Larger fixture and regression suite

Work:

- add more realistic Panorama fixtures
- add regression tests for parser, resolver, planner, and exporter behavior

PASS validation:

- regressions in import, resolution, planning, and export are caught by automated tests
- sample coverage extends beyond `Example-1.xml`

Suggested validation/tests:

- expanded automated test suite
- fixture-driven regression runs in CI

### 10.3 Deployment and operational validation

Work:

- validate Docker Compose deployment path
- document operational requirements for PostgreSQL and storage

PASS validation:

- application stack boots reliably with documented dependencies
- deployment docs reflect the real runtime architecture

Suggested validation/tests:

- docker compose smoke test
- startup/shutdown persistence test
- documented operator checklist review

## Cross-Phase Rules

- no phase should silently change locked design decisions without first updating `docs/devel/design.md`
- every completed task should leave behind automated validation where practical
- manual validation is acceptable for early scaffolding, but critical parser, resolver, planner, and exporter logic should gain automated tests as soon as possible
- frontend work must consume backend semantics, not recreate them
- change application logic must remain backend-owned and transactional
