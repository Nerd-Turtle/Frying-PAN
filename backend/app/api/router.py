from fastapi import APIRouter

from app.api.admin import router as admin_router
from app.api.auth import router as auth_router
from app.api.health import router as health_router
from app.api.organizations import router as organizations_router
from app.api.notifications import router as notifications_router
from app.api.projects import router as projects_router
from app.api.workbench import router as workbench_router

api_router = APIRouter()
api_router.include_router(admin_router)
api_router.include_router(auth_router)
api_router.include_router(health_router)
api_router.include_router(organizations_router)
api_router.include_router(notifications_router)
api_router.include_router(projects_router)
api_router.include_router(workbench_router)
