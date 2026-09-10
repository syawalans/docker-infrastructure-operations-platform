from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
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
from app.services.report_date_service import (
    ReportDateValidationError,
    report_date_service,
)
from app.services.report_service import (
    report_service,
)
from app.services.settings_service import (
    settings_service,
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


def _resolve_reporting_period(
    db: Session,
    *,
    date_from: str | None = None,
    date_to: str | None = None,
    period: str | None = None,
):
    default_period_days = settings_service.get_value(
        db,
        "reporting",
        "default_reporting_period_days",
        default=30,
    )

    timezone_name = settings_service.get_value(
        db,
        "general",
        "timezone",
        default="UTC",
    )

    return report_date_service.resolve_period(
        date_from=date_from,
        date_to=date_to,
        period_mode=period,
        default_period_days=default_period_days,
        timezone_name=timezone_name,
    )


def _bad_date_request(
    exc: ReportDateValidationError,
) -> HTTPException:
    return HTTPException(
        status_code=400,
        detail=str(exc),
    )


def _date_error_response(
    *,
    request: Request,
    current_user: UserModel,
    page_title: str,
    back_url: str,
    error: str,
):
    return templates.TemplateResponse(
        request=request,
        name="reports/date_error.html",
        context={
            "page_title": page_title,
            "active_nav": "reports",
            "current_user": current_user,
            "back_url": back_url,
            "date_error": error,
        },
        status_code=400,
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
    period: str | None = None,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(
        require_permission(
            PERMISSION_REPORT_VIEW
        )
    ),
):
    resolved_period = _resolve_reporting_period(
        db,
        date_from=date_from,
        date_to=date_to,
        period=period,
    )

    try:
        date_range = report_date_service.require_valid(
            resolved_period.date_from,
            resolved_period.date_to,
        )
    except ReportDateValidationError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    data = (
        executive_report_service
        .get_executive_report(
            db,
            date_from=date_range.date_from or None,
            date_to=date_range.date_to or None,
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
    period: str | None = None,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(
        require_permission(
            PERMISSION_REPORT_VIEW
        )
    ),
):
    resolved_period = _resolve_reporting_period(
        db,
        date_from=date_from,
        date_to=date_to,
        period=period,
    )

    date_range = report_date_service.parse(
        resolved_period.date_from,
        resolved_period.date_to,
    )

    if not date_range.is_valid:
        return _date_error_response(
            request=request,
            current_user=current_user,
            page_title=(
                "Executive Infrastructure Report"
            ),
            back_url="/reports/executive",
            error=(
                date_range.error
                or "Invalid reporting period."
            ),
        )

    data = (
        executive_report_service
        .get_executive_report(
            db,
            date_from=date_range.date_from or None,
            date_to=date_range.date_to or None,
        )
    )

    data["reporting_period"]["mode"] = (
        resolved_period.mode
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
    period: str | None = None,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(
        require_permission(
            PERMISSION_REPORT_VIEW
        )
    ),
):
    resolved_period = _resolve_reporting_period(
        db,
        date_from=date_from,
        date_to=date_to,
        period=period,
    )

    try:
        content, filename = (
            report_export_service.export_audit_activity_csv(
                db,
                actor=actor,
                action=action,
                resource_type=resource_type,
                status=status,
                date_from=(
                    resolved_period.date_from or None
                ),
                date_to=(
                    resolved_period.date_to or None
                ),
            )
        )
    except ReportDateValidationError as exc:
        raise _bad_date_request(exc) from exc

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
    period: str | None = None,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(
        require_permission(
            PERMISSION_REPORT_VIEW
        )
    ),
):
    resolved_period = _resolve_reporting_period(
        db,
        date_from=date_from,
        date_to=date_to,
        period=period,
    )

    date_range = report_date_service.parse(
        resolved_period.date_from,
        resolved_period.date_to,
    )

    if not date_range.is_valid:
        return _date_error_response(
            request=request,
            current_user=current_user,
            page_title="Audit Activity Report",
            back_url="/reports/audit",
            error=(
                date_range.error
                or "Invalid reporting period."
            ),
        )

    data = report_service.get_audit_activity_report(
        db,
        actor=actor,
        action=action,
        resource_type=resource_type,
        status=status,
        date_from=date_range.date_from or None,
        date_to=date_range.date_to or None,
    )

    return templates.TemplateResponse(
        request=request,
        name="reports/audit.html",
        context={
            "page_title": "Audit Activity Report",
            "active_nav": "reports",
            "current_user": current_user,
            "reporting_period_mode": (
                resolved_period.mode
            ),
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
    period: str | None = None,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(
        require_permission(
            PERMISSION_REPORT_VIEW
        )
    ),
):
    resolved_period = _resolve_reporting_period(
        db,
        date_from=date_from,
        date_to=date_to,
        period=period,
    )

    try:
        content, filename = (
            report_export_service.export_monitoring_csv(
                db,
                q=q,
                status=status,
                check_type=check_type,
                date_from=(
                    resolved_period.date_from or None
                ),
                date_to=(
                    resolved_period.date_to or None
                ),
            )
        )
    except ReportDateValidationError as exc:
        raise _bad_date_request(exc) from exc

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
    period: str | None = None,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(
        require_permission(
            PERMISSION_REPORT_VIEW
        )
    ),
):
    resolved_period = _resolve_reporting_period(
        db,
        date_from=date_from,
        date_to=date_to,
        period=period,
    )

    date_range = report_date_service.parse(
        resolved_period.date_from,
        resolved_period.date_to,
    )

    if not date_range.is_valid:
        return _date_error_response(
            request=request,
            current_user=current_user,
            page_title="Monitoring Report",
            back_url="/reports/monitoring",
            error=(
                date_range.error
                or "Invalid reporting period."
            ),
        )

    data = report_service.get_monitoring_report(
        db,
        q=q,
        status=status,
        check_type=check_type,
        date_from=date_range.date_from or None,
        date_to=date_range.date_to or None,
    )

    return templates.TemplateResponse(
        request=request,
        name="reports/monitoring.html",
        context={
            "page_title": "Monitoring Report",
            "active_nav": "reports",
            "current_user": current_user,
            "reporting_period_mode": (
                resolved_period.mode
            ),
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
