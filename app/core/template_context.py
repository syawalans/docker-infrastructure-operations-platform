from fastapi import Request
from fastapi.templating import Jinja2Templates

from app.core.constants import (
    PERMISSION_ASSET_CREATE,
    PERMISSION_ASSET_DELETE,
    PERMISSION_ASSET_EDIT,
    PERMISSION_MONITORING_CONFIGURE,
    PERMISSION_MONITORING_RUN_CHECK,
    PERMISSION_SETTINGS_VIEW,
    PERMISSION_USER_MANAGE,
)
from app.core.permissions import has_permission


def csrf_token(
    request: Request,
) -> str:
    return getattr(
        request.state,
        "csrf_token",
        "",
    )


def configure_template_permissions(
    templates: Jinja2Templates,
) -> None:
    templates.env.globals.update(
        {
            "has_permission": has_permission,
            "csrf_token": csrf_token,
            "PERMISSION_ASSET_CREATE": PERMISSION_ASSET_CREATE,
            "PERMISSION_ASSET_EDIT": PERMISSION_ASSET_EDIT,
            "PERMISSION_ASSET_DELETE": PERMISSION_ASSET_DELETE,
            "PERMISSION_MONITORING_CONFIGURE": (
                PERMISSION_MONITORING_CONFIGURE
            ),
            "PERMISSION_MONITORING_RUN_CHECK": (
                PERMISSION_MONITORING_RUN_CHECK
            ),
            "PERMISSION_SETTINGS_VIEW": (
                PERMISSION_SETTINGS_VIEW
            ),
            "PERMISSION_USER_MANAGE": (
                PERMISSION_USER_MANAGE
            ),
        }
    )
