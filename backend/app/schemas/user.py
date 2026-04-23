from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    username: str
    email: str | None
    display_name: str
    role: str
    status: str
    must_change_password: bool
    created_at: datetime
    updated_at: datetime


class UserDirectoryEntryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    username: str
    display_name: str


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=8, max_length=200)


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=200)
    new_password: str = Field(min_length=8, max_length=200)


class ProfileUpdateRequest(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=200)
    email: EmailStr | None = None


class AdminUserCreateRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    display_name: str = Field(min_length=1, max_length=200)
    password: str = Field(min_length=8, max_length=200)
    email: EmailStr | None = None
    role: str = Field(default="operator", max_length=50)
    must_change_password: bool = True


class AdminUserUpdateRequest(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=200)
    email: EmailStr | None = None
    role: str | None = Field(default=None, max_length=50)
    status: str | None = Field(default=None, max_length=50)
    reset_password: str | None = Field(default=None, min_length=8, max_length=200)
    must_change_password: bool | None = None
