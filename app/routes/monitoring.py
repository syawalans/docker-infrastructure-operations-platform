from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    Form,
    HTTPException,
    Request,
)
from fastapi.responses import (
    HTMLResponse,
    RedirectResponse,
)
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.constants import (
    MONITORING_CHECK_TYPES,
    PERMISSION_MONITORING_CONFIGURE,
    PERMISSION_MONITORING_RUN_CHECK,
    PERMISSION_MONITORING_VIEW,
)
from app.core.database import get_db
from app.core.permissions import require_permission
from app.core.template_context import configure_template_permissions
from app.models.user import UserModel
from app.schemas.monitoring import MonitoringConfigCreate
from app.services.asset_service import asset_service
from app.services.audit_service import audit_service
from app.services.monitoring_service import monitoring_service


router = APIRouter(
    prefix="/monitoring",
    tags=["Monitoring"],
)

BASE_DIR = Path(__file__).resolve().parent.parent

templates = Jinja2Templates(
    directory=BASE_DIR / "templates"
)

configure_template_permissions(templates)


@router.get(
    "",
    response_class=HTMLResponse,
)
def monitoring_overview(
    request: Request,
    current_user: UserModel = Depends(
        require_permission(PERMISSION_MONITORING_VIEW)
    ),
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
            "current_user": current_user,
        },
    )


@router.get(
    "/assets/{asset_id}/configure",
    response_class=HTMLResponse,
)
def monitoring_config_form(
    request: Request,
    asset_id: int,
    current_user: UserModel = Depends(
        require_permission(
            PERMISSION_MONITORING_CONFIGURE
        )
    ),
    db: Session = Depends(get_db),
):
    asset = asset_service.get_asset(
        db,
        asset_id,
    )

    if asset is None:
        raise HTTPException(
            status_code=404,
            detail="Asset not found",
        )

    config = monitoring_service.get_config_by_asset(
        db,
        asset_id,
    )

    return templates.TemplateResponse(
        request=request,
        name="monitoring/configure.html",
        context={
            "page_title": (
                f"Configure Monitoring - "
                f"{asset.hostname} - "
                f"{settings.APP_NAME}"
            ),
            "asset": asset,
            "config": config,
            "check_types": MONITORING_CHECK_TYPES,
            "error": None,
            "current_user": current_user,
        },
    )


@router.post(
    "/assets/{asset_id}/configure"
)
def monitoring_config_save(
    request: Request,
    asset_id: int,
    check_type: str = Form(...),
    target: str = Form(...),
    port: str = Form(""),
    http_path: str = Form(""),
    interval_seconds: int = Form(60),
    timeout_seconds: int = Form(5),
    enabled: bool = Form(False),
    current_user: UserModel = Depends(
        require_permission(
            PERMISSION_MONITORING_CONFIGURE
        )
    ),
    db: Session = Depends(get_db),
):
    asset = asset_service.get_asset(
        db,
        asset_id,
    )

    if asset is None:
        raise HTTPException(
            status_code=404,
            detail="Asset not found",
        )

    try:
        parsed_port = int(port) if port.strip() else None

        data = MonitoringConfigCreate(
            asset_id=asset_id,
            check_type=check_type,
            target=target.strip(),
            port=parsed_port,
            http_path=http_path.strip() or None,
            interval_seconds=interval_seconds,
            timeout_seconds=timeout_seconds,
            enabled=enabled,
        )

        config = monitoring_service.save_config(
            db,
            data,
        )

    except (ValueError, TypeError) as exc:
        config = monitoring_service.get_config_by_asset(
            db,
            asset_id,
        )

        return templates.TemplateResponse(
            request=request,
            name="monitoring/configure.html",
            context={
                "page_title": (
                    f"Configure Monitoring - "
                    f"{asset.hostname} - "
                    f"{settings.APP_NAME}"
                ),
                "asset": asset,
                "config": config,
                "check_types": MONITORING_CHECK_TYPES,
                "error": str(exc),
                "current_user": current_user,
            },
            status_code=400,
        )

    audit_service.log(
        db,
        action="MONITORING_CONFIG_UPDATED",
        resource_type="MONITORING_CONFIG",
        resource_id=config.id,
        status="SUCCESS",
        actor=current_user,
        request=request,
        details={
            "asset_id": asset.id,
            "hostname": asset.hostname,
            "check_type": config.check_type,
            "target": config.target,
            "port": config.port,
            "http_path": config.http_path,
            "interval_seconds": config.interval_seconds,
            "timeout_seconds": config.timeout_seconds,
            "enabled": config.enabled,
        },
    )

    return RedirectResponse(
        url="/monitoring",
        status_code=303,
    )


@router.post(
    "/assets/{asset_id}/delete"
)
def monitoring_config_delete(
    request: Request,
    asset_id: int,
    current_user: UserModel = Depends(
        require_permission(
            PERMISSION_MONITORING_CONFIGURE
        )
    ),
    db: Session = Depends(get_db),
):
    asset = asset_service.get_asset(
        db,
        asset_id,
    )

    if asset is None:
        raise HTTPException(
            status_code=404,
            detail="Asset not found",
        )

    config = monitoring_service.get_config_by_asset(
        db,
        asset_id,
    )

    if config is None:
        raise HTTPException(
            status_code=404,
            detail="Monitoring configuration not found",
        )

    config_id = config.id

    config_details = {
        "asset_id": asset.id,
        "hostname": asset.hostname,
        "check_type": config.check_type,
        "target": config.target,
        "port": config.port,
        "http_path": config.http_path,
        "enabled": config.enabled,
    }

    deleted = monitoring_service.delete_config(
        db,
        asset_id,
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Monitoring configuration not found",
        )

    audit_service.log(
        db,
        action="MONITORING_CONFIG_DELETED",
        resource_type="MONITORING_CONFIG",
        resource_id=config_id,
        status="SUCCESS",
        actor=current_user,
        request=request,
        details=config_details,
    )

    return RedirectResponse(
        url="/monitoring",
        status_code=303,
    )


@router.post(
    "/assets/{asset_id}/run-check"
)
def monitoring_run_check(
    request: Request,
    asset_id: int,
    current_user: UserModel = Depends(
        require_permission(
            PERMISSION_MONITORING_RUN_CHECK
        )
    ),
    db: Session = Depends(get_db),
):
    asset = asset_service.get_asset(
        db,
        asset_id,
    )

    if asset is None:
        raise HTTPException(
            status_code=404,
            detail="Asset not found",
        )

    try:
        result = monitoring_service.run_check(
            db,
            asset_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    audit_service.log(
        db,
        action="MONITORING_CHECK_RUN",
        resource_type="MONITORING_RESULT",
        resource_id=result.id,
        status="SUCCESS",
        actor=current_user,
        request=request,
        details={
            "asset_id": asset.id,
            "hostname": asset.hostname,
            "check_type": result.check_type,
            "target": result.target,
            "port": result.port,
            "http_path": result.http_path,
            "result_status": result.status,
            "response_time_ms": result.response_time_ms,
        },
    )

    return RedirectResponse(
        url="/monitoring",
        status_code=303,
    )
