from __future__ import annotations

from frying_pan.normalized.rules import NATRule


def normalize_nat_rule(name: str, scope_path: str, position: int) -> NATRule:
    # TODO: Model NAT criteria and ordering conservatively.
    return NATRule(name=name, scope_path=scope_path, position=position)
