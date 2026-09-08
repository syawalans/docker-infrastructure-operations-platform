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
    PERMISSION_USER_MANAGE,
    USER_ROLES,
)
from app.core.database import get_db
from app.core.permissions import require_permission
from app.core.template_context import (
    configure_template_permissions,
)
from app.models.user import UserModel
from app.services.audit_service import audit_service
from app.services.user_management_service import (
    user_management_service,
)


router = APIRouter(
    prefix="/users",
    tags=["User Management"],
)

BASE_DIR = Path(__file__).resolve().parent.parent

templates = Jinja2Templates(
    directory=BASE_DIR / "templates"
)

configure_template_permissions(templates)


def render_user_form(
    request: Request,
    *,
    current_user: UserModel,
    user: UserModel | None = None,
    error: str | None = None,
    form_data: dict | None = None,
    status_code: int = 200,
):
    is_edit = user is not None

    return templates.TemplateResponse(
        request=request,
        name="users/form.html",
        context={
            "page_title": (
                f"{'Edit User' if is_edit else 'Add User'}"
                f" - {settings.APP_NAME}"
            ),
            "form_title": (
                "Edit User"
                if is_edit
                else "Add User"
            ),
            "form_description": (
                "Update account access, role, and status."
                if is_edit
                else "Create a new Infrastructure Ops user account."
            ),
            "form_action": (
                f"/users/{user.id}/edit"
                if is_edit
                else "/users/new"
            ),
            "submit_label": (
                "Update User"
                if is_edit
                else "Create User"
            ),
            "user": user,
            "roles": USER_ROLES,
            "error": error,
            "form_data": form_data or {},
            "current_user": current_user,
        },
        status_code=status_code,
    )


@router.get(
    "",
    response_class=HTMLResponse,
)
def users_list(
    request: Request,
    current_user: UserModel = Depends(
        require_permission(
            PERMISSION_USER_MANAGE
        )
    ),
    db: Session = Depends(get_db),
):
    users = user_management_service.list_users(
        db
    )

    return templates.TemplateResponse(
        request=request,
        name="users/list.html",
        context={
            "page_title": (
                f"User Management - "
                f"{settings.APP_NAME}"
            ),
            "users": users,
            "current_user": current_user,
        },
    )


@router.get(
    "/new",
    response_class=HTMLResponse,
)
def user_create_form(
    request: Request,
    current_user: UserModel = Depends(
        require_permission(
            PERMISSION_USER_MANAGE
        )
    ),
):
    return render_user_form(
        request,
        current_user=current_user,
    )


@router.post(
    "/new",
    response_class=HTMLResponse,
)
def user_create(
    request: Request,
    username: str = Form(...),
    full_name: str = Form(...),
    email: str = Form(...),
    role: str = Form(...),
    current_user: UserModel = Depends(
        require_permission(
            PERMISSION_USER_MANAGE
        )
    ),
    db: Session = Depends(get_db),
):
    form_data = {
        "username": username,
        "full_name": full_name,
        "email": email,
        "role": role,
    }

    try:
        result = (
            user_management_service.create_user(
                db,
                username=username,
                full_name=full_name,
                email=email,
                role=role,
            )
        )

    except ValueError as exc:
        return render_user_form(
            request,
            current_user=current_user,
            error=str(exc),
            form_data=form_data,
            status_code=400,
        )

    audit_service.log(
        db,
        action="USER_CREATED",
        resource_type="USER",
        resource_id=result.user.id,
        status="SUCCESS",
        actor=current_user,
        request=request,
        details={
            "username": result.user.username,
            "role": result.user.role,
            "is_active": result.user.is_active,
        },
    )

    return templates.TemplateResponse(
        request=request,
        name="users/created.html",
        context={
            "page_title": (
                f"User Created - "
                f"{settings.APP_NAME}"
            ),
            "user": result.user,
            "temporary_password": (
                result.temporary_password
            ),
            "current_user": current_user,
        },
    )


@router.get(
    "/{user_id}/edit",
    response_class=HTMLResponse,
)
def user_edit_form(
    request: Request,
    user_id: int,
    current_user: UserModel = Depends(
        require_permission(
            PERMISSION_USER_MANAGE
        )
    ),
    db: Session = Depends(get_db),
):
    user = user_management_service.get_user(
        db,
        user_id,
    )

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found.",
        )

    return render_user_form(
        request,
        current_user=current_user,
        user=user,
    )


@router.post(
    "/{user_id}/edit",
    response_class=HTMLResponse,
)
def user_edit(
    request: Request,
    user_id: int,
    full_name: str = Form(...),
    email: str = Form(...),
    role: str = Form(...),
    is_active: bool = Form(False),
    current_user: UserModel = Depends(
        require_permission(
            PERMISSION_USER_MANAGE
        )
    ),
    db: Session = Depends(get_db),
):
    user = user_management_service.get_user(
        db,
        user_id,
    )

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found.",
        )

    form_data = {
        "full_name": full_name,
        "email": email,
        "role": role,
        "is_active": is_active,
    }

    try:
        updated_user = (
            user_management_service.update_user(
                db,
                actor=current_user,
                user_id=user_id,
                full_name=full_name,
                email=email,
                role=role,
                is_active=is_active,
            )
        )

    except ValueError as exc:
        return render_user_form(
            request,
            current_user=current_user,
            user=user,
            error=str(exc),
            form_data=form_data,
            status_code=400,
        )

    audit_service.log(
        db,
        action="USER_UPDATED",
        resource_type="USER",
        resource_id=updated_user.id,
        status="SUCCESS",
        actor=current_user,
        request=request,
        details={
            "username": updated_user.username,
            "role": updated_user.role,
            "is_active": updated_user.is_active,
        },
    )

    return RedirectResponse(
        url="/users",
        status_code=303,
    )


@router.post(
    "/{user_id}/reset-password",
    response_class=HTMLResponse,
)
def user_reset_password(
    request: Request,
    user_id: int,
    current_user: UserModel = Depends(
        require_permission(
            PERMISSION_USER_MANAGE
        )
    ),
    db: Session = Depends(get_db),
):
    try:
        result = (
            user_management_service.reset_password(
                db,
                actor=current_user,
                user_id=user_id,
            )
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    audit_service.log(
        db,
        action="USER_PASSWORD_RESET",
        resource_type="USER",
        resource_id=result.user.id,
        status="SUCCESS",
        actor=current_user,
        request=request,
        details={
            "username": result.user.username,
        },
    )

    return templates.TemplateResponse(
        request=request,
        name="users/reset_password.html",
        context={
            "page_title": (
                f"Password Reset - "
                f"{settings.APP_NAME}"
            ),
            "user": result.user,
            "temporary_password": (
                result.temporary_password
            ),
            "current_user": current_user,
        },
    )
