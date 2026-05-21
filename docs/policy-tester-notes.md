# Policy Tester Behavior Notes

Frying-PAN Policy Tester evaluates one offline test flow against imported,
normalized PAN-OS security policy data. The tester is intentionally
conservative: it explains what can be determined from XML and emits warnings for
runtime behavior that depends on firewall dataplane state, content updates,
User-ID, HIP, dynamic objects, or pushed Panorama/local firewall composition.

## Security Policy Order

PAN-OS evaluates security policy from top to bottom and applies the first rule
that matches the traffic. Frying-PAN preserves rule order within each imported
rulebase and records later matching rules only for explanation. Later matching
rules do not change the selected action.

## Panorama Rulebase Order

For Panorama Device Group tests, Frying-PAN evaluates inherited pre-rules before
Device Group pre-rules, then evaluates post-rules from the requested Device
Group upward toward Shared. This follows Palo Alto's documented layering model,
but offline XML imports do not include the managed firewall's local rules unless
that firewall configuration is imported separately. Device Group tests therefore
warn that local firewall rules between pre-rules and post-rules are unavailable.

## Standalone Firewall Rulebase Order

For standalone firewall XML, Frying-PAN evaluates the selected vsys local
security rulebase in position order. Intrazone and interzone default behavior is
not synthesized in Phase 2; if no imported rule matches, the result remains
`unknown` with no matched rule.

## Match Criteria

Zones match by exact selector or `any`. Frying-PAN does not infer zones from
interfaces, routes, NAT, virtual routers, or Advanced Routing state.

Address matching supports `any`, IP netmask objects, IP range objects, literal
IP/subnet selectors, and static address groups with recursive expansion and loop
protection. FQDN objects, dynamic address groups, unresolved references, and
unsupported address variants warn and do not produce a confident match.

Service matching supports `any`, `service-http`, `service-https`, TCP/UDP
service objects, destination port ranges, optional source port ranges, and
static service groups with recursive expansion and loop protection. Unsupported
protocols or unresolved service references warn and do not produce a confident
match.

Applications match `any` or an exact application hint. If a rule names explicit
applications and the test flow application is `any`, Frying-PAN treats the
application criterion as a possible match and emits a warning because App-ID is a
runtime classification.

`application-default` is treated as a possible service match with a warning
because the default port decision depends on App-ID content and runtime
classification.

User and URL category criteria match `any` or exact hints. Missing hints for
explicit rule criteria produce warnings and keep the rule as a possible match.
HIP, security profile, schedule, target, and log forwarding behavior is not
fully evaluated in Phase 2.

## Official References

- Security policy first-match behavior and top-down rule order:
  <https://docs.paloaltonetworks.com/pan-os/11-1/pan-os-admin/policy/security-policy>
- Panorama Device Group policy layering and pre/post/local/default order:
  <https://docs.paloaltonetworks.com/panorama/11-0/panorama-admin/panorama-overview/centralized-firewall-configuration-and-update-management/device-groups/device-group-policies>
- Panorama pre-rule and post-rule behavior:
  <https://docs.paloaltonetworks.com/pan-os/11-0/pan-os-panorama-api/get-started-with-the-pan-os-rest-api/work-with-policy-rules-on-panorama-rest-api>
- `application-default` behavior:
  <https://docs.paloaltonetworks.com/pan-os/11-0/pan-os-admin/app-id/application-default>
- Device Group object inheritance and references:
  <https://docs.paloaltonetworks.com/panorama/10-2/panorama-admin/panorama-overview/centralized-firewall-configuration-and-update-management/device-groups/device-group-objects>
