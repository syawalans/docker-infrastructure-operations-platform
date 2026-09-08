from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import UserModel
from app.services.auth_service import auth_service


SESSION_COOKIE_NAME = "infrastructure_ops_session"


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> UserModel | None:
    session_token = request.cookies.get(
        SESSION_COOKIE_NAME
    )

    return auth_service.get_authenticated_user(
        db,
        session_token,
    )
