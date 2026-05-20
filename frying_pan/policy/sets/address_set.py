from __future__ import annotations

from ipaddress import ip_address, ip_network

from pydantic import BaseModel, Field


class AddressSet(BaseModel):
    values: set[str] = Field(default_factory=lambda: {"any"})
    negated: bool = False

    def contains(self, value: str) -> bool:
        if "any" in self.values:
            return True
        try:
            candidate = ip_address(value)
        except ValueError:
            return value in self.values
        for configured in self.values:
            try:
                if candidate in ip_network(configured, strict=False):
                    return True
            except ValueError:
                if configured == value:
                    return True
        return False
