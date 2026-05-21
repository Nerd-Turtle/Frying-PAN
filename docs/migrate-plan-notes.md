# Migrate Plan Notes

Frying-PAN Migration plans are local, reviewable staging records for moving or
merging Palo Alto configuration intent from one imported PAN-OS source into
another imported PAN-OS target. They do not mutate source XML or target XML.

## Staged Decisions

Migration plans record source/target bindings, scope mappings, zone mappings,
object mappings, rule placement mappings, dependency inclusion decisions,
validation messages, and optional policy assurance comparisons.

Phase 6 supports planning and reporting only. A future serializer phase must
validate production XML output before any export claim is made.

## Mapping Terms

- Scope mapping maps a source Shared, Device Group, or vsys scope to a target
  Shared, Device Group, or vsys scope.
- Zone mapping maps source zone names to target zone names.
- Object mapping records whether a source object should be copied, reused,
  renamed and copied, merged, or skipped.
- Rule placement records the target scope/rulebase and append or anchor
  placement intent.
- Dependency inclusion records object dependencies that the migration plan
  should review and include before staged rules are considered complete.

## Assurance

Policy assurance compares before/after Policy Tester results for operator
provided flows. Phase 6 compares imported source and target behavior and emits
warnings because staged migration decisions are not yet serialized into a
target config for full simulation.

## Official References

- Panorama Device Group policy and pre/post/local rule order:
  <https://docs.paloaltonetworks.com/panorama/11-0/panorama-admin/panorama-overview/centralized-firewall-configuration-and-update-management/device-groups/device-group-policies>
- Device Group object inheritance:
  <https://docs.paloaltonetworks.com/panorama/10-2/panorama-admin/panorama-overview/centralized-firewall-configuration-and-update-management/device-groups/device-group-objects>
- Rule hierarchy and rule order:
  <https://docs.paloaltonetworks.com/panorama/10-1/panorama-admin/manage-firewalls/manage-device-groups/manage-the-rule-hierarchy>
- Moving or cloning rules/objects and required references:
  <https://docs.paloaltonetworks.com/panorama/11-0/panorama-admin/manage-firewalls/manage-device-groups/move-or-clone-a-policy-rule-or-object-to-a-different-device-group>
