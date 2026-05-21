from __future__ import annotations

from ipaddress import ip_address
from typing import Any

from pydantic import BaseModel, Field, field_validator


class PolicyTestCase(BaseModel):
    source_zone: str
    destination_zone: str
    source_ip: str
    destination_ip: str
    protocol: str
    destination_port: int | None = None
    source_port: int | None = None
    application: str = "any"
    user: str = "any"
    url_category: str | None = None
    source_hip: str = "any"
    destination_hip: str = "any"
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("source_ip", "destination_ip")
    @classmethod
    def _normalize_ip(cls, value: str) -> str:
        return str(ip_address(value))

    @field_validator("protocol")
    @classmethod
    def _normalize_protocol(cls, value: str) -> str:
        protocol = value.strip().lower()
        if protocol not in {"tcp", "udp"}:
            raise ValueError("Policy Tester currently supports tcp and udp test flows.")
        return protocol

    @field_validator(
        "source_zone",
        "destination_zone",
        "application",
        "user",
        "url_category",
        "source_hip",
        "destination_hip",
        mode="before",
    )
    @classmethod
    def _normalize_selector(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = str(value).strip()
        return stripped or "any"

    @field_validator("destination_port", "source_port")
    @classmethod
    def _validate_port(cls, value: int | None) -> int | None:
        if value is None:
            return None
        if value < 1 or value > 65535:
            raise ValueError("Ports must be between 1 and 65535.")
        return value
