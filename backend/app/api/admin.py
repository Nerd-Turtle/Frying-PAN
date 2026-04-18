from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import AdminUserCreateRequest, AdminUserUpdateRequest, UserRead
from app.services.admin_service import create_local_user, list_users, update_local_user
from app.services.app_audit_service import log_app_event

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=list[UserRead])
def list_users_endpoint(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
) -> list[UserRead]:
    return list_users(db=db)


@router.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user_endpoint(
    payload: AdminUserCreateRequest,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
) -> UserRead:
    user = create_local_user(db=db, payload=payload, actor=current_user)
    log_app_event(
        db=db,
        event_type="admin.user.created",
        payload=f"Administrator '{current_user.username}' created user '{user.username}'.",
        actor_user_id=current_user.id,
    )
    return user


@router.patch("/users/{user_id}", response_model=UserRead)
def update_user_endpoint(
    user_id: str,
    payload: AdminUserUpdateRequest,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
) -> UserRead:
    user = update_local_user(db=db, user_id=user_id, payload=payload, actor=current_user)
    log_app_event(
        db=db,
        event_type="admin.user.updated",
        payload=f"Administrator '{current_user.username}' updated user '{user.username}'.",
        actor_user_id=current_user.id,
    )
    return user
