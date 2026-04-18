from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import AdminUserCreateRequest, AdminUserUpdateRequest
from app.services.auth_service import (
    flush_user_or_raise,
    hash_password,
    normalize_optional_email,
    normalize_username,
    validate_user_role,
    validate_user_status,
)
from app.services.organization_service import create_organization_for_user


def list_users(db: Session) -> list[User]:
    return list(db.scalars(select(User).order_by(User.created_at.asc())).all())


def create_local_user(db: Session, payload: AdminUserCreateRequest, actor: User) -> User:
    user = User(
        username=normalize_username(db=db, username=payload.username),
        email=normalize_optional_email(db=db, email=payload.email),
        display_name=payload.display_name.strip(),
        password_hash=hash_password(payload.password),
        role=validate_user_role(payload.role),
        status="active",
        must_change_password=payload.must_change_password,
    )
    db.add(user)
    flush_user_or_raise(db)
    create_organization_for_user(
        db=db,
        user=user,
        name=f"{user.display_name} Personal",
    )
    db.commit()
    db.refresh(user)
    return user


def update_local_user(
    db: Session,
    user_id: str,
    payload: AdminUserUpdateRequest,
    actor: User,
) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    if payload.display_name is not None:
        user.display_name = payload.display_name.strip()
    if payload.email is not None:
        user.email = normalize_optional_email(db=db, email=payload.email, user_id=user.id)
    if payload.role is not None:
        user.role = validate_user_role(payload.role)
    if payload.status is not None:
        user.status = validate_user_status(payload.status)
    if payload.reset_password is not None:
        user.password_hash = hash_password(payload.reset_password)
        user.must_change_password = True
    if payload.must_change_password is not None:
        user.must_change_password = payload.must_change_password
    user.updated_at = datetime.now(timezone.utc)

    if actor.id == user.id and user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Administrators cannot disable their own account from this endpoint.",
        )

    db.add(user)
    flush_user_or_raise(db)
    db.commit()
    db.refresh(user)
    return user
