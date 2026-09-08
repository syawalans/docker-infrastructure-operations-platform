from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.constants import (
    ROLE_ADMINISTRATOR,
    USER_ROLES,
)
from app.core.security import (
    generate_temporary_password,
    hash_password,
)
from app.models.user import UserModel
from app.repositories.user_repository import user_repository


@dataclass
class UserCreationResult:
    user: UserModel
    temporary_password: str


@dataclass
class PasswordResetResult:
    user: UserModel
    temporary_password: str


class UserManagementService:
    def list_users(
        self,
        db: Session,
    ) -> list[UserModel]:
        return user_repository.list_users(db)

    def get_user(
        self,
        db: Session,
        user_id: int,
    ) -> UserModel | None:
        return user_repository.get_by_id(
            db,
            user_id,
        )

    def create_user(
        self,
        db: Session,
        *,
        username: str,
        email: str,
        full_name: str,
        role: str,
    ) -> UserCreationResult:
        username = username.strip().lower()
        email = email.strip().lower()
        full_name = full_name.strip()

        self._validate_identity_fields(
            username=username,
            email=email,
            full_name=full_name,
        )

        self._validate_role(role)

        if user_repository.get_by_username(
            db,
            username,
        ):
            raise ValueError(
                "Username is already in use."
            )

        if user_repository.get_by_email(
            db,
            email,
        ):
            raise ValueError(
                "Email address is already in use."
            )

        temporary_password = (
            generate_temporary_password()
        )

        user = user_repository.create_user(
            db,
            username=username,
            email=email,
            full_name=full_name,
            password_hash=hash_password(
                temporary_password
            ),
            role=role,
        )

        return UserCreationResult(
            user=user,
            temporary_password=temporary_password,
        )

    def update_user(
        self,
        db: Session,
        *,
        actor: UserModel,
        user_id: int,
        full_name: str,
        email: str,
        role: str,
        is_active: bool,
    ) -> UserModel:
        user = user_repository.get_by_id(
            db,
            user_id,
        )

        if user is None:
            raise ValueError(
                "User not found."
            )

        full_name = full_name.strip()
        email = email.strip().lower()

        if not full_name:
            raise ValueError(
                "Full name is required."
            )

        if not email:
            raise ValueError(
                "Email address is required."
            )

        self._validate_role(role)

        existing_email = (
            user_repository.get_by_email(
                db,
                email,
            )
        )

        if (
            existing_email is not None
            and existing_email.id != user.id
        ):
            raise ValueError(
                "Email address is already in use."
            )

        if actor.id == user.id:
            if role != ROLE_ADMINISTRATOR:
                raise ValueError(
                    "You cannot remove your own Administrator role."
                )

            if not is_active:
                raise ValueError(
                    "You cannot deactivate your own account."
                )

        updated_user = user_repository.update_user(
            db,
            user,
            full_name=full_name,
            email=email,
            role=role,
            is_active=is_active,
        )

        if not updated_user.is_active:
            user_repository.revoke_all_sessions(
                db,
                updated_user.id,
            )

        return updated_user

    def reset_password(
        self,
        db: Session,
        *,
        actor: UserModel,
        user_id: int,
    ) -> PasswordResetResult:
        user = user_repository.get_by_id(
            db,
            user_id,
        )

        if user is None:
            raise ValueError(
                "User not found."
            )

        if actor.id == user.id:
            raise ValueError(
                "Use Change Password to update your own password."
            )

        temporary_password = (
            generate_temporary_password()
        )

        user_repository.set_temporary_password(
            db,
            user,
            hash_password(
                temporary_password
            ),
        )

        user_repository.revoke_all_sessions(
            db,
            user.id,
        )

        return PasswordResetResult(
            user=user,
            temporary_password=temporary_password,
        )

    def _validate_role(
        self,
        role: str,
    ) -> None:
        if role not in USER_ROLES:
            raise ValueError(
                "Invalid user role."
            )

    def _validate_identity_fields(
        self,
        *,
        username: str,
        email: str,
        full_name: str,
    ) -> None:
        if not username:
            raise ValueError(
                "Username is required."
            )

        if not email:
            raise ValueError(
                "Email address is required."
            )

        if not full_name:
            raise ValueError(
                "Full name is required."
            )

        if len(username) > 100:
            raise ValueError(
                "Username must not exceed 100 characters."
            )

        if len(email) > 255:
            raise ValueError(
                "Email address must not exceed 255 characters."
            )

        if len(full_name) > 150:
            raise ValueError(
                "Full name must not exceed 150 characters."
            )


user_management_service = UserManagementService()
