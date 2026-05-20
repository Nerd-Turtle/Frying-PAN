from __future__ import annotations

from pydantic import BaseModel


class PolicyTestCase(BaseModel):
    source_zone: str
    destination_zone: str
    source_ip: str
    destination_ip: str
    protocol: str
    destination_port: int | None = None
    application: str = "any"
    user: str = "any"
    url_category: str | None = None
