# Modify Plan Notes

Frying-PAN Modify plans are local, reviewable staging records for one imported
PAN-OS configuration. They do not mutate source XML, and Phase 5 does not claim
production-safe XML export.

## Staged Decisions

Modify actions record operator intent, affected object or rule identifiers,
parameters, impacted references, validation warnings, and approval state.
Supported staged actions include:

- object rename
- object dedupe/reference replacement
- object move
- rule reorder inside the same scope and rulebase
- simple rule enable/disable and logging metadata changes

The plan preview and report describe what would change in normalized planning
terms. A future serializer phase must validate XML output before any production
export claim is made.

## Validation

Plan validation checks for missing source objects/rules, duplicate action
conflicts, duplicate target object names, missing target scopes, unresolved
references, and scope/rulebase boundary warnings. Validation warnings are
explicit review signals; they are not automatic blockers unless marked as
errors.

## Drag And Drop

GUI drag/drop and mapping operations must create staged plan decisions first.
They must not edit source XML directly.

## Official References

- Panorama object move/clone dependency requirements:
  <https://docs.paloaltonetworks.com/panorama/11-0/panorama-admin/manage-firewalls/manage-device-groups/move-or-clone-a-policy-rule-or-object-to-a-different-device-group>
- Device Group object inheritance and scope:
  <https://docs.paloaltonetworks.com/panorama/10-2/panorama-admin/panorama-overview/centralized-firewall-configuration-and-update-management/device-groups/device-group-objects>
- Policy rule hierarchy and order:
  <https://docs.paloaltonetworks.com/panorama/10-1/panorama-admin/manage-firewalls/manage-device-groups/manage-the-rule-hierarchy>
