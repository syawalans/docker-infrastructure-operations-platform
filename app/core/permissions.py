from collections.abc import Callable

from fastapi import Depends, HTTPException, status

from app.core.auth import get_current_user
from app.core.constants import ROLE_PERMISSIONS
from app.models.user import UserModel


def has_permission(
    user: UserModel,
    permission: str,
) -> bool:
    permissions = ROLE_PERMISSIONS.get(
        user.role,
        set(),
    )

    return permission in permissions


def require_permission(
    permission: str,
) -> Callable:
    def permission_dependency(
        current_user: UserModel | None = Depends(
            get_current_user
        ),
    ) -> UserModel:
        if current_user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required.",
            )

        if not has_permission(
            current_user,
            permission,
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action.",
            )

        return current_user

    return permission_dependency
