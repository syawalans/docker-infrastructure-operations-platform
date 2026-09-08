from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.core.auth import SESSION_COOKIE_NAME
from app.core.config import settings
from app.core.csrf_middleware import CSRFMiddleware
from app.core.database import Base, SessionLocal, engine
from app.models.asset import AssetModel
from app.models.audit import AuditLogModel
from app.models.monitoring import (
    MonitoringConfigModel,
    MonitoringResultModel,
)
from app.models.user import (
    UserModel,
    UserSessionModel,
)
from app.routes.assets import router as assets_router
from app.routes.auth import router as auth_router
from app.routes.dashboard import router as dashboard_router
from app.routes.monitoring import router as monitoring_router
from app.routes.users import router as users_router
from app.services.auth_service import auth_service


BASE_DIR = Path(__file__).resolve().parent

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
)

app.add_middleware(
    CSRFMiddleware
)

app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static",
)


@app.middleware("http")
async def authentication_middleware(
    request: Request,
    call_next,
):
    public_paths = {
        "/login",
        "/health",
    }

    path = request.url.path

    if (
        path.startswith("/static/")
        or path in public_paths
    ):
        return await call_next(request)

    db = SessionLocal()

    try:
        session_token = request.cookies.get(
            SESSION_COOKIE_NAME
        )

        current_user = auth_service.get_authenticated_user(
            db,
            session_token,
        )

        request.state.current_user = current_user

        if current_user is None:
            return RedirectResponse(
                url="/login",
                status_code=303,
            )

        if (
            current_user.must_change_password
            and path != "/change-password"
            and path != "/logout"
        ):
            return RedirectResponse(
                url="/change-password",
                status_code=303,
            )

    finally:
        db.close()

    return await call_next(request)


app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(assets_router)
app.include_router(monitoring_router)
app.include_router(users_router)


@app.get("/health", tags=["Health"])
def health():
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
    }
