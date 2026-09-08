from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.constants import PERMISSION_DASHBOARD_VIEW
from app.core.database import get_db
from app.core.permissions import require_permission
from app.core.template_context import (
    configure_template_permissions,
)
from app.models.user import UserModel
from app.services.asset_service import asset_service


router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent

templates = Jinja2Templates(
    directory=BASE_DIR / "templates"
)

configure_template_permissions(templates)


@router.get("/", response_class=HTMLResponse)
def dashboard(
    request: Request,
    current_user: UserModel = Depends(
        require_permission(
            PERMISSION_DASHBOARD_VIEW
        )
    ),
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
            "current_user": current_user,
        },
    )
