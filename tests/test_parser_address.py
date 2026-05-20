from __future__ import annotations

from frying_pan.panos.normalizers.address import normalize_address_object


def test_address_normalizer_returns_skeleton_model() -> None:
    address = normalize_address_object("web-1", "shared", "192.0.2.10/32")

    assert address.name == "web-1"
    assert address.scope_path == "shared"
    assert address.value == "192.0.2.10/32"
