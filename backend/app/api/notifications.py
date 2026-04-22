from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin_user, get_current_ready_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.notification import (
    NotificationHistoryEntryRead,
    NotificationSettingsRead,
    NotificationSettingsUpdateRequest,
)
from app.services.app_audit_service import log_app_event
from app.services.notification_service import (
    get_or_create_app_settings,
    list_notification_history,
    update_notification_timeout,
)

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/settings", response_model=NotificationSettingsRead)
def get_notification_settings_endpoint(
    current_user: User = Depends(get_current_ready_user),
    db: Session = Depends(get_db),
) -> NotificationSettingsRead:
    return get_or_create_app_settings(db=db)


@router.patch("/settings", response_model=NotificationSettingsRead)
def update_notification_settings_endpoint(
    payload: NotificationSettingsUpdateRequest,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
) -> NotificationSettingsRead:
    settings = update_notification_timeout(
        db=db,
        timeout_seconds=payload.notification_timeout_seconds,
    )
    log_app_event(
        db=db,
        event_type="admin.notifications.updated",
        payload=(
            f"Administrator '{current_user.username}' set notification timeout to "
            f"{payload.notification_timeout_seconds} seconds."
        ),
        actor_user_id=current_user.id,
    )
    return settings


@router.get("/history", response_model=list[NotificationHistoryEntryRead])
def list_notification_history_endpoint(
    current_user: User = Depends(get_current_ready_user),
    db: Session = Depends(get_db),
    limit: int = Query(default=20, ge=1, le=100),
) -> list[NotificationHistoryEntryRead]:
    return list_notification_history(db=db, user=current_user, limit=limit)
