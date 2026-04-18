from __future__ import annotations

import re

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.models.organization_membership import OrganizationMembership
from app.models.user import User


def list_user_organizations(db: Session, user_id: str) -> list[Organization]:
    statement = (
        select(Organization)
        .join(
            OrganizationMembership,
            OrganizationMembership.organization_id == Organization.id,
        )
        .where(OrganizationMembership.user_id == user_id)
        .order_by(Organization.created_at.asc())
    )
    return list(db.scalars(statement).all())


def create_organization_for_user(db: Session, user: User, name: str) -> Organization:
    organization = Organization(
        name=name.strip(),
        slug=_unique_slug_for_name(db=db, name=name),
        created_by_user_id=user.id,
    )
    membership = OrganizationMembership(
        organization=organization,
        user_id=user.id,
        role="owner",
    )
    db.add(organization)
    db.add(membership)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An organization with that name already exists.",
        ) from exc
    return organization


def require_organization_membership(
    db: Session, organization_id: str, user_id: str
) -> OrganizationMembership:
    statement = select(OrganizationMembership).where(
        OrganizationMembership.organization_id == organization_id,
        OrganizationMembership.user_id == user_id,
    )
    membership = db.scalars(statement).first()
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to that organization.",
        )
    return membership


def get_default_organization_for_user(db: Session, user_id: str) -> Organization:
    organizations = list_user_organizations(db=db, user_id=user_id)
    if not organizations:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No organization membership exists for this user.",
        )
    return organizations[0]


def _unique_slug_for_name(db: Session, name: str) -> str:
    base_slug = _slugify(name) or "organization"
    candidate = base_slug
    suffix = 2
    while db.scalars(select(Organization.id).where(Organization.slug == candidate)).first():
        candidate = f"{base_slug}-{suffix}"
        suffix += 1
    return candidate


def _slugify(name: str) -> str:
    lowered = name.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", lowered)
    return slug.strip("-")
