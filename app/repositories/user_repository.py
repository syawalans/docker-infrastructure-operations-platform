from datetime import datetime, timezone

from sqlalchemy import or_, select, update
from sqlalchemy.orm import Session

from app.models.user import UserModel, UserSessionModel


class UserRepository:
    def get_by_login(
        self,
        db: Session,
        login: str,
    ) -> UserModel | None:
        normalized_login = login.strip().lower()

        statement = select(UserModel).where(
            or_(
                UserModel.username == normalized_login,
                UserModel.email == normalized_login,
            )
        )

        return db.scalar(statement)

    def create_session(
        self,
        db: Session,
        *,
        user_id: int,
        session_token_hash: str,
        expires_at: datetime,
    ) -> UserSessionModel:
        session = UserSessionModel(
            user_id=user_id,
            session_token_hash=session_token_hash,
            expires_at=expires_at,
        )

        db.add(session)
        db.commit()
        db.refresh(session)

        return session

    def get_session_by_hash(
        self,
        db: Session,
        session_token_hash: str,
    ) -> UserSessionModel | None:
        statement = select(UserSessionModel).where(
            UserSessionModel.session_token_hash
            == session_token_hash
        )

        return db.scalar(statement)

    def mark_login(
        self,
        db: Session,
        user: UserModel,
    ) -> None:
        user.last_login_at = datetime.now(timezone.utc)

        db.add(user)
        db.commit()

    def update_password(
        self,
        db: Session,
        user: UserModel,
        password_hash: str,
    ) -> None:
        user.password_hash = password_hash
        user.must_change_password = False
        user.password_changed_at = datetime.now(timezone.utc)

        db.add(user)
        db.commit()
        db.refresh(user)

    def revoke_session(
        self,
        db: Session,
        session: UserSessionModel,
    ) -> None:
        session.revoked_at = datetime.now(timezone.utc)

        db.add(session)
        db.commit()

    def revoke_all_sessions(
        self,
        db: Session,
        user_id: int,
    ) -> None:
        now = datetime.now(timezone.utc)

        statement = (
            update(UserSessionModel)
            .where(
                UserSessionModel.user_id == user_id,
                UserSessionModel.revoked_at.is_(None),
            )
            .values(
                revoked_at=now,
            )
        )

        db.execute(statement)
        db.commit()


user_repository = UserRepository()
