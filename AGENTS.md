# AGENTS.md

## Purpose

Frying-PAN is a web-based Panorama / PAN-OS configuration merge and migration workbench.

Its job is to help an operator:

- create a project
- upload one or more exported XML configuration sources
- inspect and index those sources
- scaffold analysis and merge workflows
- eventually export a merged result

This repository is currently an MVP scaffold. It is not a finished Panorama merge engine.

## Architecture Boundaries

The architecture split is strict:

- `frontend/` owns user experience, workflow orchestration, project views, upload forms, browsing, diff/merge presentation, and conflict-resolution interfaces.
- `backend/` owns all configuration semantics, parsing, normalization, validation, diffing, merge planning, dependency analysis, and export generation.
- application/account concerns and project-scoped Panorama workbench concerns must remain separated, with `projects` acting as the boundary between them.

The frontend must never become the place where Panorama configuration meaning is implemented.

## Non-Negotiable Rules

- All Panorama/PAN-OS parsing belongs in the backend.
- All normalization into canonical internal models belongs in the backend.
- All diff logic belongs in the backend.
- All merge logic belongs in the backend.
- All dependency analysis belongs in the backend.
- All export generation belongs in the backend.
- The frontend should never directly implement config semantics.
- XML should be parsed into internal models before merge logic is applied.
- XML should be treated primarily as an import/export boundary.

If a proposed frontend change starts encoding Panorama object rules, reference matching rules, dependency graphs, or merge semantics in TypeScript, stop and move that logic to Python.

## Contributor Expectations

- Favor small, reviewable, incremental commits.
- Keep comments and naming clear.
- Prefer maintainable scaffolding over fake completeness.
- Add explicit `TODO:` markers where real Panorama-specific implementation will go.
- Keep repository structure clean and unsurprising.
- Preserve the separation between UX concerns and backend config logic.
- Contributors and coding agents are authorized to install required apps, packages, and development tools when needed to complete the task, as long as the installation is relevant, minimal, and documented in the work summary when it materially affects the environment.
- When tests require temporary local services, containers, or other runtime environments, shut them down after validation is complete unless the user explicitly asks to keep them running.

## v1 Scope Guardrails

Keep v1 focused on:

- project management
- source upload
- source inventory/indexing scaffolding
- analysis scaffolding
- merge workflow scaffolding
- export scaffolding

Do not overbuild these areas in v1:

- queueing infrastructure
- distributed workers
- Redis / Celery / RQ
- auth / SSO / RBAC beyond the current minimal local-account and session-cookie baseline
- multi-service decomposition
- fake enterprise abstractions

FastAPI background jobs are enough unless the code clearly proves otherwise.
PostgreSQL is the primary database target.
Do not treat SQLite as the architectural baseline going forward unless a task explicitly targets optional local/dev support.

## Backend Guidance

When adding backend functionality:

- Prefer a canonical model over ad hoc XML surgery.
- Isolate XML parsing in dedicated parser modules.
- Keep merge logic separate from API route handlers.
- Keep persistence concerns separate from parser and merge code.
- Keep application/account logic separate from project workbench persistence and config semantics.
- Make import/export boundaries explicit.
- Record project/source/event metadata and canonical analysis state in PostgreSQL.
- Store raw uploaded XML on disk under `storage/`.

## Frontend Guidance

When adding frontend functionality:

- Focus on workflows, visibility, state presentation, and operator confidence.
- Assume backend endpoints return the source of truth for semantic decisions.
- Do not recreate merge or dependency logic in the client.
- Keep TypeScript models aligned to backend response contracts, not independent semantics.

Good frontend work:

- project dashboard scaffolding
- upload flows
- source inventories
- comparison views
- conflict review UI
- merge workflow navigation
- export/download views

Bad frontend work:

- parsing PAN-OS XML in the browser
- deciding config dependency order in the browser
- implementing object merge behavior in the browser
- encoding Panorama naming semantics in UI helpers

## Review Heuristics

Changes are on the right track when they:

- make the backend more capable as the semantic engine
- make the frontend better as an operator workbench
- reduce coupling between XML structure and merge logic
- keep the codebase easy to run locally and via Docker Compose

Changes need rework when they:

- push config semantics into the frontend
- manipulate XML directly across many layers
- introduce speculative infrastructure without current need
- make the skeleton look more complete than it really is

## Practical Rule Of Thumb

If a feature answers “what does this Panorama config mean?” or “how should these objects merge?”, it belongs in the backend.

If a feature answers “how should the operator see, stage, review, and trigger that work?”, it belongs in the frontend.
