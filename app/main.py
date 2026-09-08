from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import Base, engine
from app.models.asset import AssetModel
from app.models.monitoring import (
    MonitoringConfigModel,
    MonitoringResultModel,
)
from app.routes.assets import router as assets_router
from app.routes.dashboard import router as dashboard_router
from app.routes.monitoring import router as monitoring_router
from app.services.monitoring_scheduler import monitoring_scheduler


BASE_DIR = Path(__file__).resolve().parent

Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    monitoring_scheduler.start()

    try:
        yield
    finally:
        monitoring_scheduler.stop()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static",
)

app.include_router(dashboard_router)
app.include_router(assets_router)
app.include_router(monitoring_router)


@app.get("/health", tags=["Health"])
def health():
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "monitoring_scheduler": (
            "enabled"
            if settings.MONITORING_SCHEDULER_ENABLED
            else "disabled"
        ),
    }
