from __future__ import annotations

from frying_pan.normalized.addresses import AddressObject


def normalize_address_object(name: str, scope_path: str, value: str | None) -> AddressObject:
    # TODO: Add PAN-OS address type handling and official documentation references.
    return AddressObject(name=name, scope_path=scope_path, value=value)
