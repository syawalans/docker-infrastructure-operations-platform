from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response
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
from app.services.executive_report_service import (
    executive_report_service,
)
from app.services.executive_pdf_service import (
    executive_pdf_service,
)
from app.services.report_export_service import (
    report_export_service,
)
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


@router.get("/executive.pdf")
def executive_report_pdf(
    date_from: str | None = None,
    date_to: str | None = None,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(
        require_permission(
            PERMISSION_REPORT_VIEW
        )
    ),
):
    data = (
        executive_report_service
        .get_executive_report(
            db,
            date_from=date_from,
            date_to=date_to,
        )
    )

    generated_by = (
        current_user.full_name
        or current_user.username
    )

    content, filename = (
        executive_pdf_service.generate_pdf(
            data,
            generated_by=generated_by,
        )
    )

    return Response(
        content=content,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; filename="{filename}"'
            )
        },
    )


@router.get("/executive")
def executive_report(
    request: Request,
    date_from: str | None = None,
    date_to: str | None = None,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(
        require_permission(
            PERMISSION_REPORT_VIEW
        )
    ),
):
    data = (
        executive_report_service
        .get_executive_report(
            db,
            date_from=date_from,
            date_to=date_to,
        )
    )

    return templates.TemplateResponse(
        request=request,
        name="reports/executive.html",
        context=data,
    )


@router.get("/audit/export.csv")
def export_audit_activity_csv(
    actor: str | None = None,
    action: str | None = None,
    resource_type: str | None = None,
    status: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(
        require_permission(
            PERMISSION_REPORT_VIEW
        )
    ),
):
    content, filename = (
        report_export_service.export_audit_activity_csv(
            db,
            actor=actor,
            action=action,
            resource_type=resource_type,
            status=status,
            date_from=date_from,
            date_to=date_to,
        )
    )

    return Response(
        content=content,
        media_type=(
            "text/csv; charset=utf-8"
        ),
        headers={
            "Content-Disposition": (
                'attachment; filename="'
                + filename
                + '"'
            )
        },
    )


@router.get("/audit")
def audit_activity_report(
    request: Request,
    actor: str | None = None,
    action: str | None = None,
    resource_type: str | None = None,
    status: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(
        require_permission(
            PERMISSION_REPORT_VIEW
        )
    ),
):
    data = report_service.get_audit_activity_report(
        db,
        actor=actor,
        action=action,
        resource_type=resource_type,
        status=status,
        date_from=date_from,
        date_to=date_to,
    )

    return templates.TemplateResponse(
        request=request,
        name="reports/audit.html",
        context={
            "page_title": "Audit Activity Report",
            "active_nav": "reports",
            "current_user": current_user,
            **data,
        },
    )


@router.get("/monitoring/export.csv")
def export_monitoring_csv(
    q: str | None = None,
    status: str | None = None,
    check_type: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(
        require_permission(
            PERMISSION_REPORT_VIEW
        )
    ),
):
    content, filename = (
        report_export_service.export_monitoring_csv(
            db,
            q=q,
            status=status,
            check_type=check_type,
            date_from=date_from,
            date_to=date_to,
        )
    )

    return Response(
        content=content,
        media_type=(
            "text/csv; charset=utf-8"
        ),
        headers={
            "Content-Disposition": (
                'attachment; filename="'
                + filename
                + '"'
            )
        },
    )


@router.get("/monitoring")
def monitoring_report(
    request: Request,
    q: str | None = None,
    status: str | None = None,
    check_type: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(
        require_permission(
            PERMISSION_REPORT_VIEW
        )
    ),
):
    data = report_service.get_monitoring_report(
        db,
        q=q,
        status=status,
        check_type=check_type,
        date_from=date_from,
        date_to=date_to,
    )

    return templates.TemplateResponse(
        request=request,
        name="reports/monitoring.html",
        context={
            "page_title": "Monitoring Report",
            "active_nav": "reports",
            "current_user": current_user,
            **data,
        },
    )


@router.get("/assets/export.csv")
def export_asset_inventory_csv(
    q: str | None = None,
    asset_type: str | None = None,
    environment: str | None = None,
    status: str | None = None,
    location: str | None = None,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(
        require_permission(
            PERMISSION_REPORT_VIEW
        )
    ),
):
    content, filename = (
        report_export_service.export_asset_inventory_csv(
            db,
            q=q,
            asset_type=asset_type,
            environment=environment,
            status=status,
            location=location,
        )
    )

    return Response(
        content=content,
        media_type=(
            "text/csv; charset=utf-8"
        ),
        headers={
            "Content-Disposition": (
                'attachment; filename="'
                + filename
                + '"'
            )
        },
    )


@router.get("/assets")
def asset_inventory_report(
    request: Request,
    q: str | None = None,
    asset_type: str | None = None,
    environment: str | None = None,
    status: str | None = None,
    location: str | None = None,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(
        require_permission(
            PERMISSION_REPORT_VIEW
        )
    ),
):
    data = (
        report_service.get_asset_inventory_report(
            db,
            q=q,
            asset_type=asset_type,
            environment=environment,
            status=status,
            location=location,
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
