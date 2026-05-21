# Dedupe And Conflict Analysis Notes

Frying-PAN dedupe and conflict analysis is read-only. It identifies review
candidates in imported normalized inventory and does not stage Modify or
Migrate decisions by itself.

## Finding Types

- Duplicate object: multiple objects have the same normalized intrinsic value.
- Same-name conflict: objects with the same name and type have different
  normalized values across scopes.
- Unused object candidate: an object was not referenced by parsed rule or group
  dependency records.
- Placement recommendation: duplicate values in multiple non-shared scopes may
  deserve Shared or ancestor Device Group placement review.
- Unsupported object: an object could not be fully fingerprinted.

## Scope And Panorama Limitations

Panorama Shared objects are inherited by Device Groups, and Device Group
descendants can override inherited object values. Frying-PAN preserves scope
context and emits conservative warnings for same-name conflicts and placement
recommendations. A finding is not a safe-to-delete or safe-to-move decision.

Unused object candidates are especially conservative because Phase 4 uses parsed
references and dependencies only. Unparsed configuration sections may still
reference an object.

## Official References

- Device Group object inheritance and scope:
  <https://docs.paloaltonetworks.com/panorama/10-2/panorama-admin/panorama-overview/centralized-firewall-configuration-and-update-management/device-groups/device-group-objects>
- Create objects for Shared or Device Group policy:
  <https://docs.paloaltonetworks.com/panorama/11-1/panorama-admin/manage-firewalls/manage-device-groups/create-objects-for-use-in-shared-or-device-group-policy>
- Object override and inherited object precedence:
  <https://docs.paloaltonetworks.com/panorama/10-2/panorama-admin/manage-firewalls/manage-device-groups/manage-precedence-of-inherited-objects>
- Moving or cloning rules/objects and required references:
  <https://docs.paloaltonetworks.com/panorama/11-0/panorama-admin/manage-firewalls/manage-device-groups/move-or-clone-a-policy-rule-or-object-to-a-different-device-group>
