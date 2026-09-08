from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.services.monitoring_service import monitoring_service


router = APIRouter(
    prefix="/monitoring",
    tags=["Monitoring"],
)

BASE_DIR = Path(__file__).resolve().parent.parent

templates = Jinja2Templates(
    directory=BASE_DIR / "templates"
)


@router.get(
    "",
    response_class=HTMLResponse,
)
def monitoring_overview(
    request: Request,
    db: Session = Depends(get_db),
):
    data = monitoring_service.get_overview(db)

    return templates.TemplateResponse(
        request=request,
        name="monitoring/overview.html",
        context={
            "page_title": f"Monitoring - {settings.APP_NAME}",
            "stats": data["stats"],
            "monitoring_items": data["items"],
        },
    )
