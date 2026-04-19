from __future__ import annotations

import base64
import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, Response, status
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.app_session import AppSession
from app.models.organization import Organization
from app.models.user import User
from app.schemas.auth import SessionRead
from app.schemas.user import ChangePasswordRequest, LoginRequest, ProfileUpdateRequest
from app.services.organization_service import create_organization_for_user, list_user_organizations

BOOTSTRAP_ADMIN_USERNAME = "chef"
BOOTSTRAP_ADMIN_DISPLAY_NAME = "Chef"
BOOTSTRAP_ADMIN_ROLE = "admin"


def ensure_bootstrap_admin(db: Session) -> None:
    settings = get_settings()
    user = db.scalars(
        select(User).where(User.username == settings.bootstrap_admin_username)
    ).first()
    if user is None:
        user = User(
            username=settings.bootstrap_admin_username,
            display_name=settings.bootstrap_admin_display_name,
            password_hash=hash_password(settings.bootstrap_admin_password),
            role="admin",
            status="active",
            must_change_password=True,
        )
        db.add(user)
        db.flush()
        create_organization_for_user(
            db=db,
            user=user,
            name=f"{user.display_name} Personal",
        )
        db.commit()
        return

    changed = False
    if user.role != "admin":
        user.role = "admin"
        changed = True
    if user.status != "active":
        user.status = "active"
        changed = True
    if user.must_change_password and not verify_password(
        settings.bootstrap_admin_password,
        user.password_hash,
    ):
        user.password_hash = hash_password(settings.bootstrap_admin_password)
        changed = True
    if changed:
        db.add(user)
        db.commit()


def authenticate_user(db: Session, payload: LoginRequest) -> User:
    username = payload.username.strip().lower()
    user = db.scalars(select(User).where(User.username == username)).first()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
        )
    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is not active.",
        )
    return user


def change_password(
    db: Session,
    user: User,
    payload: ChangePasswordRequest,
) -> User:
    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect.",
        )
    user.password_hash = hash_password(payload.new_password)
    user.must_change_password = False
    user.updated_at = datetime.now(timezone.utc)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_current_user_profile(
    db: Session,
    user: User,
    payload: ProfileUpdateRequest,
) -> User:
    if payload.display_name is not None:
        user.display_name = payload.display_name.strip()
    if payload.email is not None:
        user.email = normalize_optional_email(db=db, email=payload.email, user_id=user.id)
    user.updated_at = datetime.now(timezone.utc)
    db.add(user)
    flush_user_or_raise(db)
    db.commit()
    db.refresh(user)
    return user


def create_user_session(db: Session, user: User) -> tuple[str, AppSession]:
    raw_token = secrets.token_urlsafe(32)
    session = AppSession(
        user_id=user.id,
        token_hash=_hash_token(raw_token),
        expires_at=datetime.now(timezone.utc)
        + timedelta(hours=get_settings().session_ttl_hours),
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return raw_token, session


def resolve_user_session(db: Session, raw_token: str | None) -> tuple[User, AppSession]:
    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication is required.",
        )

    session = db.scalars(
        select(AppSession).where(AppSession.token_hash == _hash_token(raw_token))
    ).first()
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication is required.",
        )

    now = datetime.now(timezone.utc)
    expires_at = _coerce_utc(session.expires_at)
    if expires_at <= now:
        db.delete(session)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired.",
        )

    user = db.get(User, session.user_id)
    if user is None or user.status != "active":
        db.delete(session)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication is required.",
        )

    session.last_seen_at = now
    db.add(session)
    db.commit()
    db.refresh(session)
    return user, session


def destroy_user_session(db: Session, raw_token: str | None) -> None:
    if not raw_token:
        return
    db.execute(delete(AppSession).where(AppSession.token_hash == _hash_token(raw_token)))
    db.commit()


def build_session_read(db: Session, user: User, session: AppSession) -> SessionRead:
    organizations: list[Organization] = list_user_organizations(db=db, user_id=user.id)
    return SessionRead(
        user=user,
        organizations=organizations,
        session_expires_at=_coerce_utc(session.expires_at),
        password_change_required=user.must_change_password,
    )


def attach_session_cookie(response: Response, raw_token: str, session: AppSession) -> None:
    settings = get_settings()
    max_age = int(
        (_coerce_utc(session.expires_at) - datetime.now(timezone.utc)).total_seconds()
    )
    response.set_cookie(
        key=settings.session_cookie_name,
        value=raw_token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=max_age,
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(key=get_settings().session_cookie_name, path="/")


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1)
    return "scrypt$16384$8$1$" + base64.b64encode(salt).decode("ascii") + "$" + base64.b64encode(
        digest
    ).decode("ascii")


def verify_password(password: str, encoded_hash: str) -> bool:
    try:
        algorithm, n_text, r_text, p_text, salt_b64, digest_b64 = encoded_hash.split("$", 5)
    except ValueError:
        return False
    if algorithm != "scrypt":
        return False
    salt = base64.b64decode(salt_b64.encode("ascii"))
    expected = base64.b64decode(digest_b64.encode("ascii"))
    actual = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=int(n_text),
        r=int(r_text),
        p=int(p_text),
    )
    return secrets.compare_digest(actual, expected)


def normalize_optional_email(db: Session, email: str | None, user_id: str | None = None) -> str | None:
    if email is None:
        return None

    normalized = email.strip().lower()
    if not normalized:
        return None

    statement = select(User).where(User.email == normalized)
    existing = db.scalars(statement).first()
    if existing is not None and existing.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with that email already exists.",
        )
    return normalized


def normalize_username(db: Session, username: str, user_id: str | None = None) -> str:
    normalized = username.strip().lower()
    if not normalized:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Username is required.",
        )
    existing = db.scalars(select(User).where(User.username == normalized)).first()
    if existing is not None and existing.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with that username already exists.",
        )
    return normalized


def validate_user_role(role: str) -> str:
    normalized = role.strip().lower()
    if normalized not in {"admin", "operator"}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Role must be either 'admin' or 'operator'.",
        )
    return normalized


def validate_user_status(status_text: str) -> str:
    normalized = status_text.strip().lower()
    if normalized not in {"active", "disabled"}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Status must be either 'active' or 'disabled'.",
        )
    return normalized


def flush_user_or_raise(db: Session) -> None:
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User record conflicts with an existing account.",
        ) from exc


def _hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def _coerce_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
