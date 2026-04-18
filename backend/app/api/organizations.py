from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_ready_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.organization import OrganizationCreate, OrganizationRead
from app.services.organization_service import create_organization_for_user, list_user_organizations

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.get("", response_model=list[OrganizationRead])
def list_organizations_endpoint(
    current_user: User = Depends(get_current_ready_user),
    db: Session = Depends(get_db),
) -> list[OrganizationRead]:
    return list_user_organizations(db=db, user_id=current_user.id)


@router.post("", response_model=OrganizationRead, status_code=status.HTTP_201_CREATED)
def create_organization_endpoint(
    payload: OrganizationCreate,
    current_user: User = Depends(get_current_ready_user),
    db: Session = Depends(get_db),
) -> OrganizationRead:
    organization = create_organization_for_user(db=db, user=current_user, name=payload.name)
    db.commit()
    db.refresh(organization)
    return organization
