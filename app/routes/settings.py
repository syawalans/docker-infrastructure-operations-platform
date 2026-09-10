from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    Form,
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
    PERMISSION_SETTINGS_EDIT,
    PERMISSION_SETTINGS_VIEW,
)
from app.core.database import get_db
from app.core.permissions import require_permission
from app.core.settings_registry import SYSTEM_TIMEZONES
from app.core.template_context import (
    configure_template_permissions,
)
from app.models.user import UserModel
from app.services.audit_service import audit_service
from app.services.settings_service import settings_service
from app.services.system_information_service import (
    system_information_service,
)


router = APIRouter(
    prefix="/settings",
    tags=["Settings"],
)

BASE_DIR = Path(__file__).resolve().parent.parent

templates = Jinja2Templates(
    directory=BASE_DIR / "templates"
)

configure_template_permissions(templates)


def render_settings(
    request: Request,
    *,
    current_user: UserModel,
    db: Session,
    error: str | None = None,
    success: str | None = None,
    form_data: dict | None = None,
    status_code: int = 200,
):
    general = settings_service.get_category_values(
        db,
        "general",
    )

    monitoring = settings_service.get_category_values(
        db,
        "monitoring",
    )

    reporting = settings_service.get_category_values(
        db,
        "reporting",
    )

    security = {
        "session_lifetime_hours": (
            settings.AUTH_SESSION_LIFETIME_HOURS
        ),
        "login_max_attempts": (
            settings.AUTH_LOGIN_MAX_ATTEMPTS
        ),
        "login_window_seconds": (
            settings.AUTH_LOGIN_WINDOW_SECONDS
        ),
        "login_block_seconds": (
            settings.AUTH_LOGIN_BLOCK_SECONDS
        ),
        "auth_cookie_secure": (
            settings.AUTH_COOKIE_SECURE
        ),
        "csrf_cookie_secure": (
            settings.CSRF_COOKIE_SECURE
        ),
    }

    system_information = (
        system_information_service
        .get_system_information(db)
    )

    if form_data:
        form_category = form_data.get(
            "_category"
        )

        values = {
            key: value
            for key, value in form_data.items()
            if key != "_category"
        }

        if form_category == "general":
            general = {
                **general,
                **values,
            }

        if form_category == "monitoring":
            monitoring = {
                **monitoring,
                **values,
            }

        if form_category == "reporting":
            reporting = {
                **reporting,
                **values,
            }

    return templates.TemplateResponse(
        request=request,
        name="settings/index.html",
        context={
            "page_title": (
                f"Settings - {settings.APP_NAME}"
            ),
            "general": general,
            "monitoring": monitoring,
            "reporting": reporting,
            "security": security,
            "system_information": system_information,
            "check_types": MONITORING_CHECK_TYPES,
            "timezones": SYSTEM_TIMEZONES,
            "error": error,
            "success": success,
            "current_user": current_user,
        },
        status_code=status_code,
    )


@router.get(
    "",
    response_class=HTMLResponse,
)
def settings_page(
    request: Request,
    current_user: UserModel = Depends(
        require_permission(
            PERMISSION_SETTINGS_VIEW
        )
    ),
    db: Session = Depends(get_db),
):
    success = None

    saved = request.query_params.get("saved")

    if saved == "1":
        success = "General settings saved successfully."

    if saved == "monitoring":
        success = (
            "Monitoring defaults saved successfully."
        )

    if saved == "reporting":
        success = (
            "Reporting preferences saved successfully."
        )

    return render_settings(
        request,
        current_user=current_user,
        db=db,
        success=success,
    )


@router.post(
    "/general",
    response_class=HTMLResponse,
)
def general_settings_save(
    request: Request,
    platform_display_name: str = Form(...),
    organization_name: str = Form(""),
    timezone: str = Form(...),
    current_user: UserModel = Depends(
        require_permission(
            PERMISSION_SETTINGS_EDIT
        )
    ),
    db: Session = Depends(get_db),
):
    form_data = {
        "_category": "general",
        "platform_display_name": (
            platform_display_name
        ),
        "organization_name": organization_name,
        "timezone": timezone,
    }

    try:
        values = (
            settings_service.validate_general_settings(
                platform_display_name=(
                    platform_display_name
                ),
                organization_name=organization_name,
                timezone=timezone,
            )
        )

    except ValueError as exc:
        return render_settings(
            request,
            current_user=current_user,
            db=db,
            error=str(exc),
            form_data=form_data,
            status_code=400,
        )

    changes = []

    for setting_key, new_value in values.items():
        setting = settings_service.get_setting(
            db,
            "general",
            setting_key,
        )

        if setting is None:
            return render_settings(
                request,
                current_user=current_user,
                db=db,
                error=(
                    f"Required setting "
                    f"'general.{setting_key}' "
                    f"was not found."
                ),
                form_data=values,
                status_code=500,
            )

        old_value = (
            settings_service.deserialize_value(
                setting
            )
        )

        if old_value == new_value:
            continue

        updated = settings_service.update_setting(
            db,
            category="general",
            setting_key=setting_key,
            setting_value=new_value,
            updated_by=current_user.id,
        )

        changes.append(
            {
                "setting": updated,
                "old_value": old_value,
                "new_value": new_value,
            }
        )

    for change in changes:
        updated = change["setting"]

        audit_service.log(
            db,
            action="SYSTEM_SETTING_UPDATED",
            resource_type="SYSTEM_SETTING",
            resource_id=(
                f"{updated.category}."
                f"{updated.setting_key}"
            ),
            status="SUCCESS",
            actor=current_user,
            request=request,
            details={
                "setting_key": updated.setting_key,
                "old_value": change["old_value"],
                "new_value": change["new_value"],
            },
        )

    return RedirectResponse(
        url="/settings?saved=1",
        status_code=303,
    )


@router.post(
    "/monitoring",
    response_class=HTMLResponse,
)
def monitoring_defaults_save(
    request: Request,
    default_check_type: str = Form(...),
    default_interval_seconds: int = Form(...),
    default_timeout_seconds: int = Form(...),
    current_user: UserModel = Depends(
        require_permission(
            PERMISSION_SETTINGS_EDIT
        )
    ),
    db: Session = Depends(get_db),
):
    form_data = {
        "_category": "monitoring",
        "default_check_type": default_check_type,
        "default_interval_seconds": (
            default_interval_seconds
        ),
        "default_timeout_seconds": (
            default_timeout_seconds
        ),
    }

    try:
        values = (
            settings_service.validate_monitoring_defaults(
                default_check_type=default_check_type,
                default_interval_seconds=(
                    default_interval_seconds
                ),
                default_timeout_seconds=(
                    default_timeout_seconds
                ),
            )
        )

    except ValueError as exc:
        return render_settings(
            request,
            current_user=current_user,
            db=db,
            error=str(exc),
            form_data=form_data,
            status_code=400,
        )

    changes = []

    for setting_key, new_value in values.items():
        setting = settings_service.get_setting(
            db,
            "monitoring",
            setting_key,
        )

        if setting is None:
            return render_settings(
                request,
                current_user=current_user,
                db=db,
                error=(
                    f"Required setting "
                    f"'monitoring.{setting_key}' "
                    f"was not found."
                ),
                form_data=form_data,
                status_code=500,
            )

        old_value = (
            settings_service.deserialize_value(
                setting
            )
        )

        if old_value == new_value:
            continue

        updated = settings_service.update_setting(
            db,
            category="monitoring",
            setting_key=setting_key,
            setting_value=new_value,
            updated_by=current_user.id,
        )

        changes.append(
            {
                "setting": updated,
                "old_value": old_value,
                "new_value": new_value,
            }
        )

    for change in changes:
        updated = change["setting"]

        audit_service.log(
            db,
            action="SYSTEM_SETTING_UPDATED",
            resource_type="SYSTEM_SETTING",
            resource_id=(
                f"{updated.category}."
                f"{updated.setting_key}"
            ),
            status="SUCCESS",
            actor=current_user,
            request=request,
            details={
                "setting_key": updated.setting_key,
                "old_value": change["old_value"],
                "new_value": change["new_value"],
            },
        )

    return RedirectResponse(
        url="/settings?saved=monitoring",
        status_code=303,
    )


@router.post(
    "/reporting",
    response_class=HTMLResponse,
)
def reporting_preferences_save(
    request: Request,
    default_reporting_period_days: int = Form(...),
    current_user: UserModel = Depends(
        require_permission(
            PERMISSION_SETTINGS_EDIT
        )
    ),
    db: Session = Depends(get_db),
):
    form_data = {
        "_category": "reporting",
        "default_reporting_period_days": (
            default_reporting_period_days
        ),
    }

    try:
        values = (
            settings_service.validate_reporting_settings(
                default_reporting_period_days=(
                    default_reporting_period_days
                ),
            )
        )

    except ValueError as exc:
        return render_settings(
            request,
            current_user=current_user,
            db=db,
            error=str(exc),
            form_data=form_data,
            status_code=400,
        )

    changes = []

    for setting_key, new_value in values.items():
        setting = settings_service.get_setting(
            db,
            "reporting",
            setting_key,
        )

        if setting is None:
            return render_settings(
                request,
                current_user=current_user,
                db=db,
                error=(
                    f"Required setting "
                    f"'reporting.{setting_key}' "
                    f"was not found."
                ),
                form_data=form_data,
                status_code=500,
            )

        old_value = (
            settings_service.deserialize_value(
                setting
            )
        )

        if old_value == new_value:
            continue

        updated = settings_service.update_setting(
            db,
            category="reporting",
            setting_key=setting_key,
            setting_value=new_value,
            updated_by=current_user.id,
        )

        changes.append(
            {
                "setting": updated,
                "old_value": old_value,
                "new_value": new_value,
            }
        )

    for change in changes:
        updated = change["setting"]

        audit_service.log(
            db,
            action="SYSTEM_SETTING_UPDATED",
            resource_type="SYSTEM_SETTING",
            resource_id=(
                f"{updated.category}."
                f"{updated.setting_key}"
            ),
            status="SUCCESS",
            actor=current_user,
            request=request,
            details={
                "setting_key": updated.setting_key,
                "old_value": change["old_value"],
                "new_value": change["new_value"],
            },
        )

    return RedirectResponse(
        url="/settings?saved=reporting",
        status_code=303,
    )
