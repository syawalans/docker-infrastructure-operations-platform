from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.constants import (
    PERMISSION_REPORT_VIEW,
)
from app.core.database import get_db
from app.core.permissions import require_permission
from app.core.template_context import (
    configure_template_permissions,
)
from app.models.user import UserModel
from app.services.report_service import (
    report_service,
)


BASE_DIR = Path(__file__).resolve().parent.parent

templates = Jinja2Templates(
    directory=BASE_DIR / "templates"
)

configure_template_permissions(templates)

router = APIRouter(
    prefix="/reports",
    tags=["Reports"],
)


@router.get("")
def reports_overview(
    request: Request,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(
        require_permission(
            PERMISSION_REPORT_VIEW
        )
    ),
):
    data = report_service.get_overview(db)

    return templates.TemplateResponse(
        request=request,
        name="reports/overview.html",
        context={
            "page_title": "Reports",
            "active_nav": "reports",
            "current_user": current_user,
            **data,
        },
    )


@router.get("/assets")
def asset_inventory_report(
    request: Request,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(
        require_permission(
            PERMISSION_REPORT_VIEW
        )
    ),
):
    data = (
        report_service.get_asset_inventory_report(
            db
        )
    )

    return templates.TemplateResponse(
        request=request,
        name="reports/assets.html",
        context={
            "page_title": "Asset Inventory Report",
            "active_nav": "reports",
            "current_user": current_user,
            **data,
        },
    )
