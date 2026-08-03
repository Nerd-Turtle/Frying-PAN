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
Import XML
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

- Explorer
- Inventory
- Modify
- Migrate
- Convert
- Policy Audit
- Policy Tester
- Dedupe / Conflicts
- Reports
- Settings

The PySide6 shell follows a desktop IDE/workbench layout:

- workflow navigation rail for top-level product areas
- project explorer for the active portable workspace and imported sources
- one active workflow in the main area, backed by a shared page stack; workflow
  tabs are not duplicated above the content
- project and active-source context in the status bar
- native Windows file/folder dialogs and a GUI-script entry point

Explorer is the entry workspace; there is no separate Dashboard. Action labels
preserve a strict boundary: New/Open operate on portable projects, while
Import/Export operate on XML configuration files. The project tree exposes the
same actions through context menus. Export XML remains present but reports the
serializer-validation boundary until tested XML output is implemented.

New Project uses one project-configuration dialog containing the display name,
parent directory, and a live final-folder preview. The name becomes the project
folder name by default. Inline validation prevents Windows-invalid names,
occupied non-empty folders, and accidental reuse of an existing Frying-PAN
workspace before any files are written. The native directory picker is an
optional Browse action within that flow.

Project create/open and source import are real desktop workflows. Importing a
supported Palo Alto XML source parses it into the normalized model and updates
the Inventory, Policy Audit, Dedupe / Conflicts, Modify, and Policy Tester
views. GUI orchestration calls the core engine; PAN-OS semantics remain outside
the GUI package.

GUI code should stage user decisions and present state. It should not encode
Panorama semantics or mutate source XML.

## Export Position

Markdown and HTML reports are safe early export targets. Mutated XML export
must wait until parser and serializer tests provide confidence.
