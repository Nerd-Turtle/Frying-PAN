from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import get_settings
from app.db.session import SessionLocal
from app.services.app_audit_service import log_app_event
from app.services.auth_service import ensure_bootstrap_admin, resolve_user_from_session_token
from app.services.storage_service import ensure_storage_layout


@asynccontextmanager
async def lifespan(_: FastAPI):
    ensure_storage_layout()
    db = SessionLocal()
    try:
        ensure_bootstrap_admin(db)
    finally:
        db.close()
    yield


settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Backend scaffold for Panorama configuration workbench workflows.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _should_log_request_error(request: Request, status_code: int) -> bool:
    if request.url.path == "/api/auth/session":
        return False

    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        return True

    return status_code >= 500


def _log_request_error(
    request: Request,
    *,
    event_type: str,
    payload: str,
    status_code: int,
) -> None:
    if getattr(request.state, "audit_logged", False):
        return
    if not _should_log_request_error(request, status_code):
        return

    db = SessionLocal()
    try:
        actor = resolve_user_from_session_token(
            db=db,
            raw_token=request.cookies.get(settings.session_cookie_name),
        )
        log_app_event(
            db=db,
            event_type=event_type,
            payload=payload,
            actor_user_id=actor.id if actor else None,
            project_id=request.path_params.get("project_id"),
        )
    finally:
        db.close()


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    issues = exc.errors()
    payload = (
        f"{request.method} {request.url.path} failed validation: "
        + "; ".join(issue.get("msg", "Invalid request.") for issue in issues[:3])
    )
    _log_request_error(
        request,
        event_type="app.request.validation_failed",
        payload=payload,
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": issues},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail if isinstance(exc.detail, str) else "Request failed."
    _log_request_error(
        request,
        event_type="app.request.failed",
        payload=f"{request.method} {request.url.path} returned {exc.status_code}: {detail}",
        status_code=exc.status_code,
    )
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    _log_request_error(
        request,
        event_type="app.request.unhandled_error",
        payload=f"{request.method} {request.url.path} raised {type(exc).__name__}: {exc}",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error."},
    )


app.include_router(api_router, prefix="/api")
