# PAN-OS XML Notes

Status: Phase 1 planned documentation

This document records parser-relevant PAN-OS and Panorama XML structure as
Frying-PAN implements it. Keep it aligned with parser behavior and tests.

## Panorama Shared Object Paths

Planned for Phase 1.

## Panorama Device Group Object Paths

Planned for Phase 1.

## Panorama Pre-Rulebase Paths

Planned for Phase 1.

## Panorama Post-Rulebase Paths

Planned for Phase 1.

## Standalone Firewall / vsys Object Paths

Planned for Phase 1.

## Standalone Firewall / vsys Rulebase Paths

Planned for Phase 1.

## Known Parser Limitations

- Phase 0 only includes source detection and parser skeletons.
- Phase 1 will document implemented object and rule paths as parser support is
  added.
- XML mutation/export remains blocked until serializer tests exist.

## Official Palo Alto Documentation References

- PAN-OS Security Policy documentation:
  https://docs.paloaltonetworks.com/pan-os/11-1/pan-os-admin/policy/security-policy

Add more official references as parser behavior is implemented.

## Implementation Notes and Uncertainties

- Keep PAN-OS behavior conservative when official documentation is unclear.
- Add `TODO:` notes in code and documentation for unresolved XML structure or
  behavior questions.
