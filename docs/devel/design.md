# Frying-PAN Design Notes

This document captures the current locked design decisions for Frying-PAN.

It is intentionally high signal and should reflect decisions we have already made, not speculative future architecture.

## Current Direction

- Backend-first implementation
- Python backend owns config semantics
- TypeScript frontend owns operator workflow and UX
- PostgreSQL is the primary database target
- Raw Panorama XML remains on disk as source material
- XML is an import/export boundary, not the working model

## Locked Decisions

### Architecture Split

- All Panorama / PAN-OS parsing, normalization, diffing, merge logic, dependency analysis, and export generation belong in the backend.
- The frontend must never directly implement Panorama config semantics.
- The frontend is responsible for project UX, source upload flows, browsing, comparison views, conflict review, merge workflow scaffolding, and export workflow presentation.

### Backend-First Workflow

We will parse imported XML before attempting any mutation.

The intended workflow is:

1. Import one or more XML files into a project workspace.
2. Parse XML into internal canonical backend models.
3. Build inventories, references, and analysis outputs.
4. Present user-reviewable comparisons and transformation previews.
5. Apply approved changes in backend-controlled transformation steps.
6. Export generated XML from the transformed canonical state.

### Canonical Model

- Frying-PAN does not invent fictional Panorama object semantics.
- Palo Alto object types and scope definitions come from the XML.
- Frying-PAN still requires internal canonical models so the backend can reason about imported data safely and consistently.
- Canonical models exist to support normalization, comparison, dependency analysis, transformation planning, and export generation.

### XML Handling

- XML should be parsed into internal models before merge logic is applied.
- XML should not be manipulated ad hoc across route handlers, frontend code, or many unrelated backend modules.
- XML is primarily the boundary format for import and export.
- Raw uploaded XML files should be preserved on disk for traceability and reprocessing.

### Workspace / Project Model

- Frying-PAN uses a project/workspace concept.
- A project can contain multiple imported XML sources.
- Analysis, transformation previews, user decisions, and exports should all be tracked within project scope.

### Database Direction

- PostgreSQL is the locked primary database choice.
- The design should assume future multi-user, multi-project usage.
- SQLite is no longer the primary target.
- If SQLite support exists later, it should be treated as an optional lightweight local/dev mode rather than the architectural baseline.

### Database Boundary

The database design must maintain a clear separation between:

- Frying-PAN application data
- project-scoped Panorama workbench data

Application data answers questions like:

- who are the users?
- which organization or team owns a project?
- who can access a project?
- what role does a user have?
- what auth/session state exists?

Project workbench data answers questions like:

- which XML sources were imported into this project?
- which scopes and objects were parsed?
- what references exist between objects?
- what analyses were run?
- what change sets were previewed or applied?

These concerns should connect at the `projects` table boundary, but they should not be mixed together in the same modeling layer.

Example:

- `users`, `organizations`, and `project_memberships` belong to the application layer
- `sources`, `scopes`, `objects`, and `references` belong to the project workbench layer

This boundary is important because auth and collaboration rules should not leak into Panorama object parsing or merge semantics.

### Storage Model

- Raw XML files stay on disk, not primarily in the database.
- The database stores metadata, canonical object records, reference edges, analysis state, user decisions, transformation plans, audit/event records, and export bookkeeping.
- As scope expands, some selectively structured or semi-structured imported data may also be stored in the database where it improves analysis or workflow persistence.
- We should not design around storing all XML wholesale in the database at the outset.

### Deduplication Direction

Deduplication needs multiple views and should not rely on a single simplistic rule.

Planned comparison dimensions include:

- object name
- object value
- normalized object value
- scope
- object type

Examples of useful filters:

- duplicates by name
- duplicates by value
- same name with different values
- same value with different names
- duplicates across specific scopes or sources

### Normalization Policy

- Normalization is needed for accurate comparison.
- Example: IPv4 host values without an explicit CIDR may be semantically equivalent to `/32`; IPv6 host values may be semantically equivalent to `/128`.
- These kinds of transformations should not be silently auto-applied.
- The system should detect likely normalization opportunities and allow user-driven approval before changing stored working state.

### References And Dependency Graph

- Panorama configuration is reference-sensitive and fragile when dependencies are changed incorrectly.
- Frying-PAN must build and maintain a reference graph during import and analysis.
- Objects should track outbound and inbound references where possible.
- Reference analysis is required before deduplication, migration, or merge actions are applied.

### Promote To Shared

- The desired end state is not just a passive “promotion is possible” report.
- The backend should eventually support a previewable transformation that promotes eligible objects to `shared` and updates dependent references to make the result valid.
- This must be graph-aware and transactionally applied.
- A report/preview mode is still important so users can review blockers, collisions, and planned rewrites before applying changes.

### Export Direction

- Export should happen from canonical transformed backend state.
- Export should not depend on brittle text replacement against the original XML.
- Round-trip traceability back to original sources should be preserved where practical.
- V1 export should serialize from project working state, not directly from immutable imported inventory rows.
- V1 export should materialize only the currently supported object types.
- Builtin references should remain literal member values in serialized XML rather than being emitted as standalone objects.
- Unsupported or untouched imported XML sections should be considered intentionally out of scope for the v1 serializer and tracked through export metadata rather than ad hoc passthrough surgery.
- Device groups in v1 export should be emitted as Panorama `device-group` entries under the device root, with hierarchy preserved in canonical scope metadata instead of nested XML rewriting.

## Schema Direction

The schema should start small, strongly relational at the identity layer, and flexible where PAN-OS-specific payload details will evolve.

Design goals:

- stable relational keys for projects, sources, scopes, objects, and references
- `jsonb` for selectively structured payloads and evolving details
- support for multiple users, multiple projects, and multiple XML files per project
- support for previewable and auditable change workflows
- ability to expand without needing a full schema rewrite every time a new object nuance is discovered

### App Layer Tables

These tables represent the Frying-PAN application itself and should remain clearly separated from imported Panorama configuration state.

#### `users`

Purpose:

- application identities
- future authentication ownership
- audit attribution

Suggested columns:

- `id` `uuid` PK
- `email` `text` unique
- `display_name` `text`
- `status` `text`
- `created_at` `timestamptz`
- `updated_at` `timestamptz`

#### `organizations`

Purpose:

- future team or tenant boundary for shared project ownership

Suggested columns:

- `id` `uuid` PK
- `name` `text`
- `slug` `text` unique
- `created_at` `timestamptz`
- `updated_at` `timestamptz`

#### `organization_memberships`

Purpose:

- map users into organizations with a role

Suggested columns:

- `id` `uuid` PK
- `organization_id` `uuid` FK -> `organizations.id`
- `user_id` `uuid` FK -> `users.id`
- `role` `text`
- `created_at` `timestamptz`

#### `projects`

Purpose:

- top-level application and workbench boundary
- container for Panorama import and transformation activity

Suggested columns:

- `id` `uuid` PK
- `organization_id` `uuid` null FK -> `organizations.id`
- `name` `text`
- `description` `text` null
- `status` `text`
- `created_by_user_id` `uuid` null FK -> `users.id`
- `created_at` `timestamptz`
- `updated_at` `timestamptz`

Notes:

- `projects` is the bridge between app concerns and workbench concerns.
- All project workbench tables should key off `project_id`.

#### `project_memberships`

Purpose:

- project-level access control without polluting workbench tables

Suggested columns:

- `id` `uuid` PK
- `project_id` `uuid` FK -> `projects.id`
- `user_id` `uuid` FK -> `users.id`
- `role` `text`
- `created_at` `timestamptz`

#### `audit_events`

Purpose:

- application-side activity history
- user attribution for meaningful actions

Suggested columns:

- `id` `uuid` PK
- `project_id` `uuid` null FK -> `projects.id`
- `actor_user_id` `uuid` null FK -> `users.id`
- `event_type` `text`
- `payload` `jsonb`
- `created_at` `timestamptz`

### Project Workbench Tables

These tables represent imported Panorama data and analysis workflow state for a project.

#### `sources`

Purpose:

- one row per imported XML file
- anchor raw XML stored on disk

Suggested columns:

- `id` `uuid` PK
- `project_id` `uuid` FK -> `projects.id`
- `label` `text`
- `filename` `text`
- `storage_path` `text`
- `file_sha256` `text`
- `source_type` `text`
- `parse_status` `text`
- `imported_by_user_id` `uuid` null FK -> `users.id`
- `imported_at` `timestamptz`
- `metadata` `jsonb`

#### `scopes`

Purpose:

- represent `shared`, device groups, nested device groups, templates, template stacks, vsys, and similar scope containers

Suggested columns:

- `id` `uuid` PK
- `project_id` `uuid` FK -> `projects.id`
- `source_id` `uuid` FK -> `sources.id`
- `parent_scope_id` `uuid` null FK -> `scopes.id`
- `scope_type` `text`
- `scope_name` `text`
- `scope_path` `text`
- `readonly_id` `text` null
- `metadata` `jsonb`

Notes:

- `scope_path` should provide a stable human-readable path within a project/source.
- `parent_scope_id` supports nested scopes such as child device groups.

#### `objects`

Purpose:

- canonical inventory of parsed Panorama objects and rules

Suggested columns:

- `id` `uuid` PK
- `project_id` `uuid` FK -> `projects.id`
- `source_id` `uuid` FK -> `sources.id`
- `scope_id` `uuid` FK -> `scopes.id`
- `object_type` `text`
- `object_name` `text`
- `raw_payload` `jsonb`
- `normalized_payload` `jsonb`
- `normalized_hash` `text` null
- `source_xpath` `text` null
- `parse_status` `text`
- `metadata` `jsonb`
- `created_at` `timestamptz`

Notes:

- `raw_payload` preserves the parsed source shape we imported.
- `normalized_payload` is what comparisons and planning should use.
- `normalized_hash` supports fast duplicate-by-value queries.
- Rules can initially live in this table as object rows to keep the first schema smaller.

#### `references`

Purpose:

- model the dependency graph between objects, groups, rules, and other referenced items

Suggested columns:

- `id` `uuid` PK
- `project_id` `uuid` FK -> `projects.id`
- `source_id` `uuid` FK -> `sources.id`
- `owner_object_id` `uuid` FK -> `objects.id`
- `reference_kind` `text`
- `reference_path` `text`
- `target_name` `text`
- `target_type_hint` `text` null
- `target_scope_hint` `text` null
- `resolved_object_id` `uuid` null FK -> `objects.id`
- `resolution_status` `text`
- `metadata` `jsonb`

Notes:

- `target_name` captures what the XML literally referenced.
- `resolved_object_id` captures the backend’s best current resolution of that reference.
- This table is central for safe deduplication, promotion, and rewrite planning.

#### `analysis_runs`

Purpose:

- track imports, inventory builds, dedup analysis, promotion analysis, validation runs, and similar project-scoped processing

Suggested columns:

- `id` `uuid` PK
- `project_id` `uuid` FK -> `projects.id`
- `source_id` `uuid` null FK -> `sources.id`
- `requested_by_user_id` `uuid` null FK -> `users.id`
- `analysis_type` `text`
- `status` `text`
- `requested_at` `timestamptz`
- `started_at` `timestamptz` null
- `finished_at` `timestamptz` null
- `parameters` `jsonb`
- `summary` `jsonb`
- `errors` `jsonb`

#### `change_sets`

Purpose:

- group together user-approved previewable project changes
- represent change intent before or during apply

Suggested columns:

- `id` `uuid` PK
- `project_id` `uuid` FK -> `projects.id`
- `created_by_user_id` `uuid` null FK -> `users.id`
- `name` `text`
- `description` `text` null
- `status` `text`
- `created_at` `timestamptz`
- `applied_at` `timestamptz` null
- `preview_summary` `jsonb`
- `operations_payload` `jsonb`

Notes:

- A change set is the right initial abstraction for “promote to shared and rewrite dependent references.”
- Users think in batches of reviewed changes more naturally than isolated atomic operations.

#### `exports`

Purpose:

- persist generated XML artifacts produced from project working state
- maintain traceability between a project, an optional applied change set, and the generated file on disk

Suggested columns:

- `id` `uuid` PK
- `project_id` `uuid` FK -> `projects.id`
- `change_set_id` `uuid` null FK -> `change_sets.id`
- `filename` `text`
- `storage_path` `text`
- `file_sha256` `text`
- `export_status` `text`
- `metadata` `jsonb`
- `created_at` `timestamptz`

Notes:

- export rows are bookkeeping records for artifacts written to disk, not substitutes for canonical object inventory
- export metadata should capture serializer version, object/scope counts, and any intentionally unsupported export boundary details

### Schema Boundary Rule

The app layer should know:

- who the user is
- which project they can access
- what they are allowed to do

The project workbench layer should know:

- what was imported
- how Panorama objects and scopes are represented
- what references exist
- what analyses and changes are pending or applied

The app layer must not encode Panorama semantics.
The project workbench layer must not encode authentication or membership logic.

`projects` is the boundary object that connects the two layers.

### Indexing Direction

Initial indexes should focus on project scoping, dedup filters, and reference traversal.

Suggested early indexes:

- `sources(project_id)`
- `scopes(source_id, scope_path)` unique
- `objects(project_id, object_type)`
- `objects(source_id, scope_id, object_type, object_name)` unique
- `objects(project_id, normalized_hash)`
- `references(owner_object_id)`
- `references(resolved_object_id)`
- `analysis_runs(project_id, analysis_type, status)`
- `change_sets(project_id, status)`

### Evolution Strategy

- Keep identity, ownership, and relationships relational.
- Use `jsonb` for evolving object-specific payloads and analysis summaries.
- Avoid PostgreSQL enums initially; prefer `text` with application validation so the schema stays easier to evolve.
- Keep imported source state distinct from user-approved change state.
- Split specialized subtype tables later only when real query or workflow pressure justifies them.

## Working-State Mutation Model

Imported source state remains immutable for planning purposes.

Phase 6 introduces a separate working-state layer so approved changes can be applied without overwriting imported source rows:

- `objects` and `references` remain the imported canonical inventory derived from source XML
- `working_objects` and `working_references` represent the current mutable project working state
- working rows keep provenance through `source_object_id` and `source_reference_id`
- working rows also record `last_change_set_id` so applied changes remain auditable

Working-state behavior:

- the first successful apply clones the full imported object/reference graph into working-state tables for that project
- later applies mutate only the working-state layer
- imported rows continue to preserve original source payloads, scope provenance, and reference resolution history
- change-set apply is transactional: either the working-state mutations and change-set status update all commit, or the project remains unchanged

This model keeps source provenance intact while creating a stable backend-owned state for future export generation.

Export generation behavior:

- export reads from `working_objects`, not directly from `objects`
- export artifacts are written to disk and recorded in the `exports` table
- export may optionally be tied back to the applied `change_set` that produced the working state being serialized

## V1 Canonical Records

The first parser and persistence pass should use a small set of canonical record shapes derived from the sample Panorama XML.

These records are intended to support:

- multi-source import
- scope-aware inventory
- duplicate detection
- reference resolution
- previewable transformation planning

### V1 Object Coverage

The initial object set should focus on:

- address objects
- address groups
- services
- service groups
- tags
- scope hierarchy

Basic rule references are also important, but full rule parsing can follow immediately after the initial object/reference pass if needed.

### Scope Record

A scope record represents the container where imported objects live.

Examples from the sample XML include:

- `shared`
- `Device-Group-1`
- `Device-Group-2`
- `DG1-Sub-Group`

The parser should derive parent-child scope relationships from the XML, including Panorama metadata such as readonly device-group parent links.

Suggested canonical shape:

```json
{
  "project_id": "uuid",
  "source_id": "uuid",
  "scope_type": "device_group",
  "scope_name": "DG1-Sub-Group",
  "scope_path": "shared/device-group:Device-Group-1/device-group:DG1-Sub-Group",
  "parent_scope_path": "shared/device-group:Device-Group-1",
  "readonly_id": "14",
  "metadata": {
    "description": "DG1 Sub Group",
    "source_xpath": "/config/devices/entry/device-group/entry[@name='DG1-Sub-Group']"
  }
}
```

Working rule:

- object identity must include source, scope, object type, and object name
- object name alone is not enough to uniquely identify imported configuration state

### Object Record

An object record captures:

- where an object came from
- what Panorama object type it is
- a parsed source payload
- a normalized payload used for comparison and planning

Example address object shape:

```json
{
  "project_id": "uuid",
  "source_id": "uuid",
  "scope_path": "shared",
  "object_type": "address",
  "object_name": "Shared-IP-Netmask",
  "raw_payload": {
    "value_kind": "ip-netmask",
    "value": "192.168.1.1/24"
  },
  "normalized_payload": {
    "value_kind": "ip-netmask",
    "ip_version": 4,
    "address_text": "192.168.1.1/24"
  },
  "parse_status": "parsed",
  "metadata": {
    "source_xpath": "/config/shared/address/entry[@name='Shared-IP-Netmask']"
  }
}
```

Example address-group shape:

```json
{
  "project_id": "uuid",
  "source_id": "uuid",
  "scope_path": "shared/device-group:Device-Group-1",
  "object_type": "address_group",
  "object_name": "DG1-Group",
  "raw_payload": {
    "group_kind": "static",
    "members": ["DG1-IP-Netmask"]
  },
  "normalized_payload": {
    "group_kind": "static",
    "members_ordered": ["DG1-IP-Netmask"]
  },
  "parse_status": "parsed",
  "metadata": {
    "source_xpath": "/config/devices/entry/device-group/entry[@name='Device-Group-1']/address-group/entry[@name='DG1-Group']"
  }
}
```

Example service-group shape:

```json
{
  "project_id": "uuid",
  "source_id": "uuid",
  "scope_path": "shared",
  "object_type": "service_group",
  "object_name": "Shared-Service-Group",
  "raw_payload": {
    "members": ["service-http"]
  },
  "normalized_payload": {
    "members_ordered": ["service-http"]
  },
  "parse_status": "parsed"
}
```

Normalization rules:

- structural normalization is encouraged
- policy-changing normalization must not be silently applied

Example:

- `172.16.1.1` and `172.16.1.1/32` may be treated as a likely normalization candidate during analysis
- the system should not automatically rewrite the stored working value without user approval

Suggested normalization suggestion shape:

```json
{
  "suggested_normalizations": [
    {
      "kind": "host_ipv4_to_cidr",
      "from": "172.16.1.1",
      "to": "172.16.1.1/32"
    }
  ]
}
```

### Reference Record

A reference record captures a dependency edge between one imported object and another resolved target or builtin target.

Example local device-group member reference:

```json
{
  "project_id": "uuid",
  "source_id": "uuid",
  "owner_object_type": "address_group",
  "owner_object_name": "DG1-Group",
  "owner_scope_path": "shared/device-group:Device-Group-1",
  "reference_kind": "group_member",
  "reference_path": "static/member[1]",
  "target_name": "DG1-IP-Netmask",
  "target_type_hints": ["address", "address_group"],
  "resolution_status": "resolved",
  "resolved_scope_path": "shared/device-group:Device-Group-1",
  "resolved_object_name": "DG1-IP-Netmask"
}
```

Example ancestor/shared reference:

```json
{
  "project_id": "uuid",
  "source_id": "uuid",
  "owner_object_type": "address_group",
  "owner_object_name": "Nested-Groups",
  "owner_scope_path": "shared/device-group:Device-Group-1",
  "reference_kind": "group_member",
  "reference_path": "static/member[2]",
  "target_name": "Shared-Group",
  "target_type_hints": ["address", "address_group"],
  "resolution_status": "resolved_in_ancestor",
  "resolved_scope_path": "shared",
  "resolved_object_name": "Shared-Group"
}
```

Example builtin reference:

```json
{
  "project_id": "uuid",
  "source_id": "uuid",
  "owner_object_type": "service_group",
  "owner_object_name": "Shared-Service-Group",
  "owner_scope_path": "shared",
  "reference_kind": "group_member",
  "reference_path": "members/member[1]",
  "target_name": "service-http",
  "target_type_hints": ["service", "service_group", "builtin_service"],
  "resolution_status": "builtin",
  "resolved_builtin_key": "service-http"
}
```

Reference records should preserve both:

- what the XML literally referenced
- what the backend resolved that reference to, if anything

### V1 Resolution Rules

Initial resolution behavior should follow these rules:

- references in `shared` resolve within `shared` first, then builtin/system namespaces where applicable
- references in a device group resolve in the current device group first, then ancestor device groups, then `shared`, then builtin/system namespaces
- child device-group scope lookup must use parent links discovered from Panorama metadata
- unresolved references must be stored explicitly
- ambiguous references must be stored explicitly

Important note:

- object precedence behavior may be influenced by Panorama settings such as ancestor-object precedence
- precedence-related behavior should be modeled as project/source configuration and not hardcoded invisibly in parser logic

### V1 Analysis Outputs Enabled By These Records

With these records in place, the backend should be able to report:

- duplicate-by-value addresses across scopes
- same-name object collisions across scopes
- mixed-scope dependency chains
- builtin references
- likely normalization suggestions for user review

Examples from the sample XML:

- `Shared-IP-Netmask`, `DG1-IP-Netmask`, `DG2-IP-Netmask`, and `DG1-SG-IP-Netmask` are duplicate-by-value candidates
- `US` and `DUP-IP-ADDRESS` are same-name comparison candidates across scopes
- `Nested-Groups` demonstrates mixed local and shared references
- `service-http` and `application-default` are builtin-style references that should be tracked differently from imported project objects

## Initial Implementation Focus

The earliest backend milestones should focus on:

- discovering scopes from imported XML
- extracting a narrow first set of object types
- building object inventories
- building reference edges
- surfacing duplicates and conflicts for review

Suggested early object types:

- address objects
- address groups
- services
- service groups
- tags

Rules are also important, but object inventory and references should come first.

## Explicit Non-Goals For Now

- no fake “fully working” Panorama merge engine yet
- no speculative distributed architecture
- no Redis / Celery / RQ unless the codebase proves the need
- no enterprise auth as a default assumption
- no frontend-owned config semantics
