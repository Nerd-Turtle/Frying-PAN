from __future__ import annotations

from frying_pan.normalized.rules import RuleAction, SecurityRule


def normalize_security_rule(name: str, scope_path: str, position: int) -> SecurityRule:
    # TODO: Normalize match criteria and security profiles from PAN-OS XML.
    return SecurityRule(
        name=name, scope_path=scope_path, position=position, action=RuleAction.UNKNOWN
    )
