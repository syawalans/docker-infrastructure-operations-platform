from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.config import settings
from app.services.asset_service import asset_service

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@router.get("/", response_class=HTMLResponse)
def dashboard(
    request: Request,
    db: Session = Depends(get_db),
):
    dashboard_data = asset_service.get_dashboard_data(db)

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "page_title": settings.APP_NAME,
            "stats": dashboard_data,
            "assets": dashboard_data["assets"],
        },
    )