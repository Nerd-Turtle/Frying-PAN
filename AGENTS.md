# AGENTS.md

## Product Direction

Frying-PAN is an offline Python desktop application for Palo Alto Networks
Panorama / PAN-OS configuration analysis, modification planning, migration
planning, conversion preparation, policy audit, policy assurance, and policy
testing.

Normal users should be able to download the app, run it locally, import config
files, analyze or stage work, and export local reports without hosting a web
application.

## Non-Negotiable Architecture Rules

- Do not reintroduce FastAPI, Next.js, PostgreSQL, login/auth, Docker-first
  deployment, or multi-user server architecture unless explicitly requested by
  the project owner.
- Use PySide6/Qt for the desktop GUI.
- Use SQLite only as a local project cache/index inside portable workspaces.
- Keep GUI logic separate from domain logic.
- Core engine modules must be usable by the GUI, CLI, tests, future batch mode,
  and a future optional API mode if one is explicitly requested later.
- Raw XML is an import/export boundary, not the primary internal model.
- Do not mutate source XML directly during GUI drag/drop or plan staging.
- Drag/drop and mapping operations must create staged plan decisions first.
- Do not claim production-safe XML export until parser and serializer tests
  exist.

## Palo Alto Networks Behavior

- Use official Palo Alto Networks documentation as the primary source for
  PAN-OS and Panorama behavior.
- When code encodes PAN-OS behavior, include a short comment referencing the
  official documentation URL.
- If official documentation does not clearly answer a behavior, keep the
  implementation conservative and add a `TODO:` noting the uncertainty.
- Policy logic must emit warnings when offline behavior cannot be fully
  determined.

This especially applies to:

- security rule evaluation order and first-match behavior
- Device Group inheritance and object overrides
- Shared versus Device Group object behavior
- Panorama pre-rulebase and post-rulebase behavior
- application-default behavior
- URL Category matching behavior
- NAT/security policy ordering where relevant
- template and template-stack behavior
- standalone firewall versus Panorama XML structure differences

## Workflow Terminology

Use these product terms consistently in code and UI:

- **Modify** or **Modification** for single Palo Alto XML change planning.
- **Migrate** or **Migration** for moving or merging Palo Alto XML
  configurations into another Palo Alto configuration.
- **Convert** or **Conversion** for non-Palo Alto source material converted into
  normalized Palo-compatible import packages.
- **Policy Audit** for full rulebase analysis.
- **Policy Assurance** for before/after behavior comparison.
- **Policy Tester** for evaluating a single test flow.

## Implementation Expectations

- Prefer small, reviewable changes.
- Preserve useful docs, parser research, and branding when replacing old
  implementation.
- Keep comments and naming clear.
- Add explicit `TODO:` markers where real Panorama-specific implementation will
  go.
- Prefer maintainable scaffolding over fake completeness.
- Add tests for parser, resolver, policy matching, policy audit, and plan
  behavior as those areas evolve.
- Prefer explicit warnings and limitations over generated guesses.

## Phase and Task Execution

Frying-PAN uses a roadmap-driven development process.

The roadmap tracks high-level Phases.

Each Phase document tracks implementation Tasks.

A Phase may be too large for one Codex prompt/session. When that happens, break
the Phase into Tasks and complete one or more Tasks per session until the Phase
is complete.

Do not mark a Phase complete unless every Task in that Phase is complete and
the full phase validation suite passes.

Do not mark a Task complete unless its implementation is done, task-specific
validation passes, related tests are added or updated, and documentation is
updated where applicable.

Use these statuses consistently:

- planned
- in-progress
- blocked
- complete

Every completed Task must include validation evidence, such as:

- pytest results
- ruff results
- CLI command output
- GUI/offscreen construction validation
- parser fixture validation
- report generation validation
- documentation update confirmation

If validation cannot be performed, leave the Task as blocked or in-progress and
document why.

Never mark work complete based only on code changes.

## Scope Guardrails

Initial rebuild work should focus on:

- desktop app shell
- local project workspace model
- source import model
- source type detection
- normalized model skeleton
- SQLite cache/index foundation
- CLI test entry points
- policy match/audit/assurance module skeletons
- Modify/Migrate/Convert plan skeletons
- README and contributor documentation

Avoid in the initial rebuild:

- workers, Redis, Celery, RQ
- SSO/RBAC/login/auth
- hosted REST API-first design
- speculative distributed infrastructure
- direct XML mutation
- fake production export claims

## Practical Rule Of Thumb

If a feature answers "what does this configuration mean?" or "how would this
policy behave?", it belongs in core Python modules.

If a feature answers "how should the operator see, stage, review, and trigger
that work?", it belongs in the PySide6 GUI.
