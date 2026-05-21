# PAN-OS XML Notes

Status: Phase 1 active documentation

This document records parser-relevant PAN-OS and Panorama XML structure as
Frying-PAN implements it. Keep it aligned with parser behavior and tests.

## Source Detection

Implemented detection currently treats a source as PAN-OS XML when the document
root is `<config>`.

Structural fields emitted by `detect_source`:

- `panos_version`: from the root `version` attribute, falling back to
  `panos-version`
- `has_shared_scope`: true when `/config/shared` exists
- `supports_device_groups`: true when
  `/config/devices/entry/device-group/entry` exists
- `has_vsys`: true when `/config/devices/entry/vsys/entry` exists
- `has_templates`: true when `/config/devices/entry/template/entry` exists
- `has_template_stacks`: true when
  `/config/devices/entry/template-stack/entry` exists

Parser selection:

- Device Group entries select `panorama_xml`.
- Firewall-style `vsys` entries without Device Groups select `firewall_xml`.
- A `<config>` root without either recognized layout selects
  `unknown_panos_xml` and emits a warning.
- XML parse failures select `unknown` and emit a parse warning.

If a file contains both Device Group and firewall-style `vsys` layouts, detection
selects Panorama and emits an ambiguity warning. Template-local `vsys` entries
under `/config/devices/entry/template/...` do not count as standalone firewall
`vsys` scopes.

## Panorama Shared Object Paths

Official Palo Alto XPath guidance documents Panorama Shared objects under:

```text
/config/shared/<object>
```

Reference fixture paths currently present for parser work:

```text
/config/shared/address/entry
/config/shared/address-group/entry
/config/shared/service/entry
/config/shared/service-group/entry
/config/shared/tag/entry
/config/shared/application-group/entry
/config/shared/profiles/custom-url-category/entry
/config/shared/profile-group/entry
/config/shared/external-list/entry
```

Object availability behavior is broader than Phase 1 parsing: official Panorama
documentation says Shared objects are available in all Device Groups. Phase 1
will record references and warnings conservatively before attempting full
inheritance behavior.

## Panorama Device Group Object Paths

Official Palo Alto XPath guidance documents Panorama Device Group objects under:

```text
/config/devices/entry[@name='localhost.localdomain']/device-group/entry[@name='<device-group-name>']/<object>
```

Reference fixture paths currently present for parser work:

```text
/config/devices/entry[@name='localhost.localdomain']/device-group/entry/address/entry
/config/devices/entry[@name='localhost.localdomain']/device-group/entry/address-group/entry
/config/devices/entry[@name='localhost.localdomain']/device-group/entry/service/entry
```

The Phase 1 reference fixture includes a parent Device Group object and a child
Device Group object with the same name to exercise override-aware inventory
modeling later in the phase. Until explicit resolver behavior is implemented,
parsers should preserve scope metadata and avoid guessing which object wins.

## Panorama Pre-Rulebase Paths

Reference fixture paths currently present for parser work:

```text
/config/devices/entry[@name='localhost.localdomain']/device-group/entry/pre-rulebase/security/rules/entry
/config/devices/entry[@name='localhost.localdomain']/device-group/entry/pre-rulebase/nat/rules/entry
```

Official Panorama documentation describes Pre Rules as Panorama-managed rules
added to the top of rule order and evaluated before local firewall rules.
Phase 1 inventory parsing should preserve rulebase location and order but should
not claim complete policy-behavior evaluation.

## Panorama Post-Rulebase Paths

Reference fixture paths currently present for parser work:

```text
/config/devices/entry[@name='localhost.localdomain']/device-group/entry/post-rulebase/security/rules/entry
```

Official Panorama documentation describes Post Rules as Panorama-managed rules
evaluated after local firewall rules. Phase 1 inventory parsing should preserve
rulebase location and order and emit limitations where local firewall rule
context is unavailable.

## Panorama Template and Template Stack Paths

Reference fixture paths currently present for parser work:

```text
/config/devices/entry[@name='localhost.localdomain']/template/entry
/config/devices/entry[@name='localhost.localdomain']/template/entry/config/devices/entry/vsys/entry
/config/devices/entry[@name='localhost.localdomain']/template/entry/config/devices/entry/network/interface/ethernet/entry
/config/devices/entry[@name='localhost.localdomain']/template/entry/config/devices/entry/network/virtual-router/entry
/config/devices/entry[@name='localhost.localdomain']/template-stack/entry
```

Official Panorama documentation describes templates as the mechanism for Device
and Network tab configuration, and template stacks as layered combinations of
templates. Phase 1 detection reports templates and template stacks, but parser
support should remain inventory-oriented until template-stack merge behavior is
implemented and tested.

## Standalone Firewall / vsys Object Paths

Official Palo Alto XPath guidance documents firewall `vsys` objects under:

```text
/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='<vsys-name>']/<object>
```

Planned Phase 1 parser paths:

```text
/config/devices/entry[@name='localhost.localdomain']/vsys/entry/address/entry
/config/devices/entry[@name='localhost.localdomain']/vsys/entry/address-group/entry
/config/devices/entry[@name='localhost.localdomain']/vsys/entry/service/entry
/config/devices/entry[@name='localhost.localdomain']/vsys/entry/service-group/entry
/config/devices/entry[@name='localhost.localdomain']/vsys/entry/tag/entry
```

## Standalone Firewall / vsys Rulebase Paths

Official Palo Alto XML API examples show firewall security rulebase queries under
`/config/devices/entry/vsys/entry/rulebase/security`.

Planned Phase 1 parser paths:

```text
/config/devices/entry[@name='localhost.localdomain']/vsys/entry/rulebase/security/rules/entry
```

## Standalone Firewall Routing Fixture Paths

Frying-PAN keeps two full standalone firewall reference fixtures so parser work
can compare matching security/object configuration across the two PAN-OS routing
engines:

```text
tests/fixtures/firewall/reference_config_items_virtual_router.xml
tests/fixtures/firewall/reference_config_items_advanced_routing.xml
```

The legacy virtual-router fixture uses:

```text
/config/devices/entry[@name='localhost.localdomain']/deviceconfig/setting/advance-routing = no
/config/devices/entry[@name='localhost.localdomain']/network/virtual-router/entry
/config/devices/entry[@name='localhost.localdomain']/network/virtual-router/entry/interface/member
/config/devices/entry[@name='localhost.localdomain']/network/virtual-router/entry/routing-table/ip/static-route/entry
```

The advanced-routing fixture uses:

```text
/config/devices/entry[@name='localhost.localdomain']/deviceconfig/setting/advance-routing = yes
/config/devices/entry[@name='localhost.localdomain']/network/logical-router/entry
/config/devices/entry[@name='localhost.localdomain']/network/logical-router/entry/vrf/entry[@name='default']
/config/devices/entry[@name='localhost.localdomain']/network/logical-router/entry/vrf/entry/interface/member
/config/devices/entry[@name='localhost.localdomain']/network/logical-router/entry/vrf/entry/routing-table/ip/static-route/entry
```

Official Palo Alto Networks documentation says switching between the legacy and
advanced routing engines requires commit and reboot before the selected engine is
effective at runtime. These fixtures are static parser references, not runtime
forwarding validation.

## Known Parser Limitations

- Phase 1 implements source detection, the first Panorama parser foundation for
  shared objects, Device Group objects, tags, and security pre/post rules, and
  the first standalone firewall `vsys` parser foundation for local objects,
  tags, and security rules. It also includes reference extraction, dependency
  mapping, CLI inventory, Markdown reports, and basic GUI inventory display.
- The reference fixture includes NAT and template examples, but Phase 1 has not
  yet implemented NAT normalization or template-stack merge behavior.
- Dynamic address group filter semantics and External Dynamic List behavior are
  not interpreted yet.
- Device Group inheritance and object override resolution are not implemented
  yet. Preserve scope metadata and emit limitations instead of guessing.
- Security policy behavior remains conservative. Phase 1 inventories rule match
  fields and references, but it does not claim complete runtime equivalence for
  App-ID, URL category, User-ID, HIP, or dynamic object behavior.
- XML mutation/export remains blocked until serializer tests exist.

## Official Palo Alto Documentation References

- PAN-OS XML API, XML and XPath:
  https://docs.paloaltonetworks.com/pan-os/11-0/pan-os-panorama-api/about-the-pan-os-xml-api/structure-of-a-pan-os-xml-api-request/xml-and-xpath
- PAN-OS XML API, use XPath to get active configuration:
  https://docs.paloaltonetworks.com/pan-os/11-0/pan-os-panorama-api/pan-os-xml-api-request-types/configuration-api/get-active-configuration/use-xpath-to-get-active-configuration
- PAN-OS CLI partial-load XPath location formats:
  https://docs.paloaltonetworks.com/pan-os/11-0/pan-os-cli-quick-start/use-the-cli/load-configurations/load-a-partial-configuration/xpath-location-formats-determined-by-device-configuration
- Panorama Device Groups:
  https://docs.paloaltonetworks.com/panorama/11-0/panorama-admin/panorama-overview/centralized-firewall-configuration-and-update-management/device-groups
- Panorama Device Group Policies:
  https://docs.paloaltonetworks.com/panorama/11-0/panorama-admin/panorama-overview/centralized-firewall-configuration-and-update-management/device-groups/device-group-policies
- Panorama objects in Shared or Device Group policy:
  https://docs.paloaltonetworks.com/panorama/11-0/panorama-admin/manage-firewalls/manage-device-groups/create-objects-for-use-in-shared-or-device-group-policy
- Panorama policy rules:
  https://docs.paloaltonetworks.com/pan-os/11-2/pan-os-web-interface-help/panorama-web-interface/defining-policies-on-panorama
- Panorama templates and template stacks:
  https://docs.paloaltonetworks.com/panorama/10-2/panorama-admin/panorama-overview/centralized-firewall-configuration-and-update-management/templates-and-template-stacks
- Enable Advanced Routing:
  https://docs.paloaltonetworks.com/ngfw/networking/networking/advanced-routing/enable-advanced-routing
- Configure a Logical Router:
  https://docs.paloaltonetworks.com/ngfw/networking/advanced-routing/configure-a-logical-router
- Network > Routing > Logical Routers:
  https://docs.paloaltonetworks.com/pan-os/11-1/pan-os-web-interface-help/network/network-routing-logical-routers
- Network > Virtual Routers:
  https://docs.paloaltonetworks.com/pan-os/11-2/pan-os-web-interface-help/network/network-virtual-routers
- PAN-OS Security Policy documentation:
  https://docs.paloaltonetworks.com/pan-os/11-1/pan-os-admin/policy/security-policy

## Implementation Notes and Uncertainties

- Treat official docs as the source for behavior and lab-exported XML as a
  source for fixture-specific element paths.
- Keep PAN-OS behavior conservative when official documentation is unclear.
- Add `TODO:` notes in code and documentation for unresolved XML structure or
  behavior questions.
- Do not mutate source XML during parsing, GUI staging, drag/drop, or reporting.
