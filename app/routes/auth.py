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

from app.core.auth import (
    SESSION_COOKIE_NAME,
    get_current_user,
)
from app.core.config import settings
from app.core.database import get_db
from app.models.user import UserModel
from app.services.auth_service import auth_service


router = APIRouter(
    tags=["Authentication"],
)

BASE_DIR = Path(__file__).resolve().parent.parent

templates = Jinja2Templates(
    directory=BASE_DIR / "templates"
)


def set_session_cookie(
    response: RedirectResponse,
    session_token: str,
) -> None:
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_token,
        max_age=(
            settings.AUTH_SESSION_LIFETIME_HOURS
            * 60
            * 60
        ),
        httponly=True,
        samesite="lax",
        secure=False,
        path="/",
    )


def render_login(
    request: Request,
    *,
    error: str | None = None,
):
    return templates.TemplateResponse(
        request=request,
        name="auth/login.html",
        context={
            "page_title": f"Login - {settings.APP_NAME}",
            "app_name": settings.APP_NAME,
            "error": error,
        },
    )


def render_change_password(
    request: Request,
    *,
    error: str | None = None,
):
    return templates.TemplateResponse(
        request=request,
        name="auth/change_password.html",
        context={
            "page_title": (
                f"Change Password - {settings.APP_NAME}"
            ),
            "error": error,
        },
    )


@router.get(
    "/login",
    response_class=HTMLResponse,
)
def login_form(
    request: Request,
    current_user: UserModel | None = Depends(
        get_current_user
    ),
):
    if current_user is not None:
        if current_user.must_change_password:
            return RedirectResponse(
                url="/change-password",
                status_code=303,
            )

        return RedirectResponse(
            url="/",
            status_code=303,
        )

    return render_login(request)


@router.post("/login")
def login(
    request: Request,
    login: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    result = auth_service.authenticate(
        db,
        login=login,
        password=password,
    )

    if result is None:
        return render_login(
            request,
            error="Invalid username, email, or password.",
        )

    destination = (
        "/change-password"
        if result.user.must_change_password
        else "/"
    )

    response = RedirectResponse(
        url=destination,
        status_code=303,
    )

    set_session_cookie(
        response,
        result.session_token,
    )

    return response


@router.get(
    "/change-password",
    response_class=HTMLResponse,
)
def change_password_form(
    request: Request,
    current_user: UserModel | None = Depends(
        get_current_user
    ),
):
    if current_user is None:
        return RedirectResponse(
            url="/login",
            status_code=303,
        )

    if not current_user.must_change_password:
        return RedirectResponse(
            url="/",
            status_code=303,
        )

    return render_change_password(
        request,
    )


@router.post("/change-password")
def change_password(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    current_user: UserModel | None = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    if current_user is None:
        return RedirectResponse(
            url="/login",
            status_code=303,
        )

    try:
        new_session_token = auth_service.change_password(
            db,
            user=current_user,
            current_password=current_password,
            new_password=new_password,
            confirm_password=confirm_password,
        )

    except ValueError as exc:
        return render_change_password(
            request,
            error=str(exc),
        )

    response = RedirectResponse(
        url="/",
        status_code=303,
    )

    set_session_cookie(
        response,
        new_session_token,
    )

    return response


@router.post("/logout")
def logout(
    request: Request,
    db: Session = Depends(get_db),
):
    session_token = request.cookies.get(
        SESSION_COOKIE_NAME
    )

    auth_service.logout(
        db,
        session_token,
    )

    response = RedirectResponse(
        url="/login",
        status_code=303,
    )

    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        path="/",
        httponly=True,
        samesite="lax",
    )

    return response
