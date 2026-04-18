<p align="center">
  <img src="frontend/public/branding/logo-readme.png" alt="Frying-PAN logo" width="480">
</p>

<p align="center">Panorama / PAN-OS configuration merge and migration workbench</p>

Frying-PAN is a web-based Panorama / PAN-OS configuration merge and migration workbench.

The project is intended to help administrators import exported XML configurations from one or more Palo Alto Networks Panorama instances, inspect and index them, compare sources, stage merge decisions, resolve naming and dependency conflicts, and eventually generate a merged output suitable for later import into another Panorama.

This is deliberately not infrastructure-as-code tooling. Frying-PAN is a configuration workbench focused on XML import, analysis, diff, merge, validation, and export with a modern Web UI and a Python backend.

## Status

This repository is an initial scaffold.

- PostgreSQL is the locked primary database target.
- The current scaffold still contains placeholder persistence code that will be brought into alignment during the early roadmap phases.
- Source XML upload is scaffolded and stores raw files on disk.
- Analysis, diff/merge, and export flows are placeholder endpoints and UI sections.
- There is no production-ready Panorama merge engine here yet.

## Design Principles

- Keep Panorama/PAN-OS parsing, normalization, diff, merge, dependency analysis, and export logic in Python on the backend.
- Keep the frontend focused on UX: project management, uploads, browsing, review workflows, and conflict-resolution interfaces.
- Store raw uploaded XML files on disk.
- Use PostgreSQL for application data and project workbench state.
- Keep a clear boundary between Frying-PAN application data and project-scoped Panorama workbench data.
- Normalize XML into internal canonical models before applying merge or diff logic.
- Treat XML as an import/export boundary, not as the primary in-memory working model.
- Prefer a clean, maintainable skeleton over fake completeness.

## MVP Scope

The v1 scaffold is intentionally narrow:

- Project creation
- Source XML upload
- Source inventory/indexing scaffold
- Placeholder analysis pipeline
- Placeholder diff/merge workflow
- Export scaffold

Out of scope for now:

- A production-ready Panorama merge engine
- Enterprise auth or SSO
- Distributed workers, Redis, Celery, or RQ
- IaC abstraction layers

## Repository Layout

```text
/
  frontend/                # Next.js + TypeScript app
  backend/                 # FastAPI app
  storage/                 # bind-mount friendly local app data
    uploads/
    projects/
    exports/
  docker-compose.yml
  .env.example
  README.md
  AGENTS.md
```

## Backend Layout

```text
backend/
  app/
    api/
    core/
    db/
    models/
    schemas/
    services/
    parsers/
    merge/
    main.py
  tests/
  requirements.txt
  Dockerfile
```

## Frontend Layout

```text
frontend/
  app/
  components/
  lib/
  public/
  src/
  package.json
  tsconfig.json
  Dockerfile
```

## Quick Start

1. Copy `.env.example` to `.env` if you want to customize local settings.
2. Run `docker compose up --build`.
3. Open `http://localhost:3000` for the frontend.
4. Open `http://localhost:8000/docs` for the backend API docs.

The default local setup mounts `./storage` into the backend container so uploaded XML files and generated project artifacts survive container restarts.

## Local Development Notes

Frontend:

- Next.js + TypeScript
- Minimal dashboard scaffold for project creation and XML upload
- Placeholder UI cards for analysis, merge, and export workflows

Backend:

- FastAPI
- PostgreSQL as the primary database target
- Alembic for schema migrations
- Raw uploads written to disk under `storage/uploads/`
- Placeholder parser and merge modules with explicit TODO markers

## Current API Surface

The starter backend currently exposes:

- `GET /api/health`
- `GET /api/projects`
- `POST /api/projects`
- `GET /api/projects/{project_id}`
- `POST /api/projects/{project_id}/sources/upload`
- `POST /api/projects/{project_id}/analysis/run`
- `POST /api/projects/{project_id}/merge/preview`
- `POST /api/projects/{project_id}/exports`

Only project creation, listing, detail retrieval, and source upload have meaningful starter behavior right now. The rest are honest scaffolds for future work.

## Database Migrations

Backend schema changes should go through Alembic.

From `backend/`:

```bash
alembic upgrade head
alembic downgrade -1
alembic revision -m "describe change"
```

The application should not rely on implicit `create_all()` behavior at startup. Migration state is the source of truth for database structure.

In the Docker Compose development path, the backend service runs `alembic upgrade head` before starting Uvicorn. For local non-Docker development, run Alembic explicitly before exercising schema-dependent routes.

If you are moving from the earlier pre-Alembic scaffold that auto-created tables at startup, reset the local development database before first booting the migration-driven stack. In Docker Compose that typically means `docker compose down -v`.

## Development Priorities

- Build the canonical backend data model for Panorama configuration objects
- Parse XML into normalized internal models
- Add source inventory and dependency-index scaffolding
- Design merge conflict models before implementing merge logic
- Keep commits incremental and reviewable

## Working Agreement

Read [AGENTS.md](/opt/frying-pan/AGENTS.md) before making substantial changes. It defines architecture boundaries and scope guardrails for contributors and coding agents.
Read [design.md](/opt/frying-pan/docs/devel/design.md) for locked design decisions and [roadmap.md](/opt/frying-pan/docs/devel/roadmap.md) for the current implementation phases.
