# Policy Audit Behavior Notes

Frying-PAN Policy Audit is a read-only review aid for imported PAN-OS security
policy. Findings are signals for operator review, not automatic remediation and
not proof that a live firewall will behave a certain way in every runtime
condition.

## Rule Order And Scope

PAN-OS evaluates security policy from top to bottom and applies the first rule
that matches traffic. Audit checks that reason about order use the same
conservative ordering model as Policy Tester.

For standalone firewall XML, Frying-PAN audits local security rules in the
selected `vsys` order. For Panorama Device Group XML, Frying-PAN evaluates
inherited pre-rules, Device Group pre-rules, Device Group post-rules, and
inherited post-rules using the documented Panorama order. Offline Panorama
audits warn that managed firewall local rules are unavailable unless a firewall
configuration is imported separately.

## Findings

Audit findings include a category, severity, affected rule names, affected
criteria, explanation, recommendation, confidence, and warnings. The current
Phase 3 checks are intentionally deterministic:

- unresolved references from parsed rules and objects
- duplicate rules with identical normalized criteria and action
- obvious full shadows where an earlier rule plainly covers a later rule
- broad allow rules
- explicit cleanup rule posture and missing explicit cleanup advisories
- disabled rules
- rules missing parsed log-at-session-end settings
- App-ID/service combinations that depend on runtime classification

Frying-PAN does not currently infer route-derived zones, NAT side effects,
security profile runtime impact, User-ID group expansion, HIP state, or
application content update details during audit.

## Shadowing

Full-shadow findings are emitted only for obvious cases where supported rule
selectors show that an earlier rule covers the later rule. Unsupported criteria
or unresolved object behavior prevents confident shadow conclusions and is
reported as warnings or separate unresolved-reference findings.

## Broad Allows And Cleanup

Broad allow findings identify rules that allow traffic with broad `any` source,
destination, application, service, user, and URL category selectors. Cleanup
findings identify explicit last-rule catch-all posture. Missing cleanup findings
are advisory because PAN-OS predefined default rules are not synthesized by
Phase 3.

## App-ID And Service Review

Rules using `application-default`, explicit applications with service `any`, or
application `any` with explicit service selectors are not automatically wrong.
They are review findings because App-ID, default-port enforcement, and content
updates are runtime-dependent.

## Official References

- Security policy first-match behavior and top-down order:
  <https://docs.paloaltonetworks.com/pan-os/11-1/pan-os-admin/policy/security-policy>
- Rule hierarchy and ordering importance:
  <https://docs.paloaltonetworks.com/panorama/10-1/panorama-admin/manage-firewalls/manage-device-groups/manage-the-rule-hierarchy>
- Panorama Device Group pre/post/local/default order:
  <https://docs.paloaltonetworks.com/panorama/11-0/panorama-admin/panorama-overview/centralized-firewall-configuration-and-update-management/device-groups/device-group-policies>
- `application-default` behavior:
  <https://docs.paloaltonetworks.com/pan-os/11-0/pan-os-admin/app-id/application-default>
- Security policy logging fields:
  <https://docs.paloaltonetworks.com/pan-os/11-2/pan-os-web-interface-help/policies/policies-security/building-blocks-in-a-security-policy-rule>
