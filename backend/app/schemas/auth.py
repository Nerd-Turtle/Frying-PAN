from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.organization import OrganizationRead
from app.schemas.user import UserRead


class SessionRead(BaseModel):
    user: UserRead
    organizations: list[OrganizationRead] = Field(default_factory=list)
    session_expires_at: datetime
    password_change_required: bool
