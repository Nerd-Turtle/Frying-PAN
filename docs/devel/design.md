# Frying-PAN Desktop Design Notes

Frying-PAN is now an offline-first Python desktop workbench.

## Locked Direction

- PySide6/Qt desktop app for normal users.
- Python core engine owns parsing, normalization, policy logic, dependency
  analysis, plan models, and exports.
- SQLite is a local cache/index inside a portable project folder.
- No hosted web frontend, REST-first backend, auth system, or external database
  is part of the default architecture.

## Core Pipeline

```text
Import Sources
Detect Source Type
Parse to Normalized ConfigScopes
Resolve Objects and Dependencies
Analyze Inventory / Conflicts / Dedupe
Run Policy Match / Policy Audit / Policy Assurance
Create Modification, Migration, or Conversion Plan
Export Report first
Export XML later
```

Raw XML remains an import/export boundary. Internal analysis should operate on
normalized configuration entities and scopes.

## Workspace Model

A Frying-PAN project is a portable local folder with a small JSON manifest,
source files, local cache, exports, and logs. The folder can be zipped and
shared with another engineer.

SQLite should never become an external service dependency.

## UI Model

The GUI uses the same top-level workflow terminology as the product:

- Dashboard
- Sources
- Modify
- Migrate
- Convert
- Policy Audit
- Policy Tester
- Reports
- Settings

GUI code should stage user decisions and present state. It should not encode
Panorama semantics or mutate source XML.

## Export Position

Markdown and HTML reports are safe early export targets. Mutated XML export
must wait until parser and serializer tests provide confidence.
