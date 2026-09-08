from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    generate_session_token,
    hash_password,
    hash_session_token,
    validate_password,
    verify_password,
)
from app.models.user import UserModel
from app.repositories.user_repository import user_repository


@dataclass
class AuthenticationResult:
    user: UserModel
    session_token: str


class AuthService:
    def create_session(
        self,
        db: Session,
        user: UserModel,
    ) -> str:
        raw_token = generate_session_token()
        token_hash = hash_session_token(raw_token)

        expires_at = (
            datetime.now(timezone.utc)
            + timedelta(
                hours=settings.AUTH_SESSION_LIFETIME_HOURS
            )
        )

        user_repository.create_session(
            db,
            user_id=user.id,
            session_token_hash=token_hash,
            expires_at=expires_at,
        )

        return raw_token

    def authenticate(
        self,
        db: Session,
        *,
        login: str,
        password: str,
    ) -> AuthenticationResult | None:
        user = user_repository.get_by_login(
            db,
            login,
        )

        if user is None:
            return None

        if not user.is_active:
            return None

        if not verify_password(
            password,
            user.password_hash,
        ):
            return None

        raw_token = self.create_session(
            db,
            user,
        )

        user_repository.mark_login(
            db,
            user,
        )

        return AuthenticationResult(
            user=user,
            session_token=raw_token,
        )

    def get_authenticated_user(
        self,
        db: Session,
        session_token: str | None,
    ) -> UserModel | None:
        if not session_token:
            return None

        token_hash = hash_session_token(
            session_token
        )

        session = user_repository.get_session_by_hash(
            db,
            token_hash,
        )

        if session is None:
            return None

        if session.revoked_at is not None:
            return None

        now = datetime.now(timezone.utc)

        if session.expires_at <= now:
            return None

        user = session.user

        if user is None:
            return None

        if not user.is_active:
            return None

        return user

    def change_password(
        self,
        db: Session,
        *,
        user: UserModel,
        current_password: str,
        new_password: str,
        confirm_password: str,
    ) -> str:
        if not verify_password(
            current_password,
            user.password_hash,
        ):
            raise ValueError(
                "Current password is incorrect."
            )

        if new_password != confirm_password:
            raise ValueError(
                "New password and confirmation do not match."
            )

        if verify_password(
            new_password,
            user.password_hash,
        ):
            raise ValueError(
                "New password must be different from the current password."
            )

        validate_password(new_password)

        new_password_hash = hash_password(
            new_password
        )

        user_repository.update_password(
            db,
            user,
            new_password_hash,
        )

        user_repository.revoke_all_sessions(
            db,
            user.id,
        )

        return self.create_session(
            db,
            user,
        )

    def logout(
        self,
        db: Session,
        session_token: str | None,
    ) -> None:
        if not session_token:
            return

        token_hash = hash_session_token(
            session_token
        )

        session = user_repository.get_session_by_hash(
            db,
            token_hash,
        )

        if session is None:
            return

        if session.revoked_at is not None:
            return

        user_repository.revoke_session(
            db,
            session,
        )


auth_service = AuthService()
