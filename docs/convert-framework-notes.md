# Convert Framework Notes

Phase 7 defines the local conversion framework used to turn future
non-Palo Alto source material into normalized Palo-compatible planning inputs.
It does not provide production-ready third-party vendor migration, and it does
not export mutated Palo Alto XML.

## Terminology

- **Convert** means read non-Palo Alto or generic source material and produce a
  normalized import package that Frying-PAN can review locally.
- **Migrate** means plan movement or merging between Palo Alto normalized
  configurations.
- **Modify** means plan changes inside a single Palo Alto normalized
  configuration.

Converted import packages can feed later planning workflows, but those
workflows still stage decisions first. Conversion never mutates source files or
target XML directly.

## Package Shape

A converted import package contains:

- source metadata and the original local source path
- normalized scopes
- normalized address, address group, service, service group, and tag records
- normalized security rules with deterministic ordering
- extracted references and dependencies
- structured conversion warnings
- unsupported feature records
- package validation errors and warnings

The package is a local Pydantic model with stable JSON serialization. Raw vendor
syntax stays outside the normalized model.

## Adapter Contract

Vendor adapters are offline, local-file adapters. Each adapter must decide
whether it can parse a path and must return a `ConvertedImportPackage` with
structured warnings instead of hiding lossy or unsupported behavior.

The Phase 7 proof path is intentionally generic JSON. It exists to validate the
framework contract, CLI, GUI, and reports. It is not a FortiGate, ASA, or other
vendor-complete parser.

## Warnings And Unsupported Behavior

Conversion warnings preserve review-required behavior such as dynamic address
group filters, unsupported rule criteria, unsupported protocols, ambiguous
source fields, and unresolved references.

Unsupported behavior is reportable but not silently transformed. If a future
adapter cannot confidently map behavior into the normalized model, it should
emit a warning or unsupported feature and keep the package reviewable.

## XML Export Boundary

Converted packages are planning inputs only. Production-safe Palo Alto XML
export remains blocked until parser and serializer tests exist.
