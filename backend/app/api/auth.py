from fastapi import APIRouter, Depends, Request, Response, status
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
from app.services.app_audit_service import log_app_event

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=SessionRead)
def login_endpoint(
    request: Request,
    payload: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> SessionRead:
    try:
        user = authenticate_user(db=db, payload=payload)
    except Exception:
        request.state.audit_logged = True
        log_app_event(
            db=db,
            event_type="auth.login.failed",
            payload=f"Failed sign-in attempt for username '{payload.username.strip().lower()}'.",
        )
        raise
    raw_token, session = create_user_session(db=db, user=user)
    log_app_event(
        db=db,
        event_type="auth.login.succeeded",
        payload=f"User '{user.username}' signed in.",
        actor_user_id=user.id,
    )
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
    log_app_event(
        db=db,
        event_type="auth.password.changed",
        payload=f"User '{updated.username}' changed their password.",
        actor_user_id=updated.id,
    )
    db.refresh(session)
    return build_session_read(db=db, user=updated, session=session)


@router.patch("/profile", response_model=UserRead)
def update_profile_endpoint(
    payload: ProfileUpdateRequest,
    authenticated: tuple = Depends(get_current_session),
    db: Session = Depends(get_db),
) -> UserRead:
    user, _ = authenticated
    updated = update_current_user_profile(db=db, user=user, payload=payload)
    log_app_event(
        db=db,
        event_type="auth.profile.updated",
        payload=f"User '{updated.username}' updated their profile.",
        actor_user_id=updated.id,
    )
    return updated


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout_endpoint(
    response: Response,
    authenticated: tuple = Depends(get_current_session),
    db: Session = Depends(get_db),
) -> Response:
    user, session = authenticated
    log_app_event(
        db=db,
        event_type="auth.logout",
        payload=f"User '{user.username}' signed out.",
        actor_user_id=user.id,
    )
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
