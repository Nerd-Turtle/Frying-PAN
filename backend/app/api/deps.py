from fastapi import Cookie, Depends
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.models.app_session import AppSession
from app.models.user import User
from app.services.auth_service import resolve_user_session


def get_current_session(
    session_token: str | None = Cookie(
        default=None,
        alias=get_settings().session_cookie_name,
    ),
    db: Session = Depends(get_db),
) -> tuple[User, AppSession]:
    return resolve_user_session(db=db, raw_token=session_token)


def get_current_user(
    authenticated: tuple[User, AppSession] = Depends(get_current_session),
) -> User:
    return authenticated[0]
