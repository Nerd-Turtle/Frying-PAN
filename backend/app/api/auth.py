from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_session
from app.db.session import get_db
from app.schemas.auth import SessionRead
from app.schemas.user import ChangePasswordRequest, LoginRequest, ProfileUpdateRequest, UserRead
from app.services.auth_service import (
    attach_session_cookie,
    authenticate_user,
    build_session_read,
    change_password,
    clear_session_cookie,
    create_user_session,
    update_current_user_profile,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=SessionRead)
def login_endpoint(
    payload: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> SessionRead:
    user = authenticate_user(db=db, payload=payload)
    raw_token, session = create_user_session(db=db, user=user)
    attach_session_cookie(response=response, raw_token=raw_token, session=session)
    return build_session_read(db=db, user=user, session=session)


@router.post("/change-password", response_model=SessionRead)
def change_password_endpoint(
    payload: ChangePasswordRequest,
    authenticated: tuple = Depends(get_current_session),
    db: Session = Depends(get_db),
) -> SessionRead:
    user, session = authenticated
    updated = change_password(db=db, user=user, payload=payload)
    db.refresh(session)
    return build_session_read(db=db, user=updated, session=session)


@router.patch("/profile", response_model=UserRead)
def update_profile_endpoint(
    payload: ProfileUpdateRequest,
    authenticated: tuple = Depends(get_current_session),
    db: Session = Depends(get_db),
) -> UserRead:
    user, _ = authenticated
    return update_current_user_profile(db=db, user=user, payload=payload)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout_endpoint(
    response: Response,
    authenticated: tuple = Depends(get_current_session),
    db: Session = Depends(get_db),
) -> Response:
    _, session = authenticated
    db.delete(session)
    db.commit()
    clear_session_cookie(response)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.get("/session", response_model=SessionRead)
def session_endpoint(
    authenticated: tuple = Depends(get_current_session),
    db: Session = Depends(get_db),
) -> SessionRead:
    user, session = authenticated
    return build_session_read(db=db, user=user, session=session)
