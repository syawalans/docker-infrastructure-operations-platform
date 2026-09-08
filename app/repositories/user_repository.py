from datetime import datetime, timezone

from sqlalchemy import or_, select, update
from sqlalchemy.orm import Session

from app.models.user import UserModel, UserSessionModel


class UserRepository:
    def list_users(
        self,
        db: Session,
    ) -> list[UserModel]:
        statement = (
            select(UserModel)
            .order_by(
                UserModel.full_name.asc(),
                UserModel.username.asc(),
            )
        )

        return list(
            db.scalars(statement).all()
        )

    def get_by_id(
        self,
        db: Session,
        user_id: int,
    ) -> UserModel | None:
        return db.get(
            UserModel,
            user_id,
        )

    def get_by_username(
        self,
        db: Session,
        username: str,
    ) -> UserModel | None:
        normalized_username = (
            username.strip().lower()
        )

        statement = select(UserModel).where(
            UserModel.username
            == normalized_username
        )

        return db.scalar(statement)

    def get_by_email(
        self,
        db: Session,
        email: str,
    ) -> UserModel | None:
        normalized_email = email.strip().lower()

        statement = select(UserModel).where(
            UserModel.email
            == normalized_email
        )

        return db.scalar(statement)

    def get_by_login(
        self,
        db: Session,
        login: str,
    ) -> UserModel | None:
        normalized_login = login.strip().lower()

        statement = select(UserModel).where(
            or_(
                UserModel.username
                == normalized_login,
                UserModel.email
                == normalized_login,
            )
        )

        return db.scalar(statement)

    def create_user(
        self,
        db: Session,
        *,
        username: str,
        email: str,
        full_name: str,
        password_hash: str,
        role: str,
    ) -> UserModel:
        user = UserModel(
            username=username.strip().lower(),
            email=email.strip().lower(),
            full_name=full_name.strip(),
            password_hash=password_hash,
            role=role,
            is_active=True,
            must_change_password=True,
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        return user

    def update_user(
        self,
        db: Session,
        user: UserModel,
        *,
        full_name: str,
        email: str,
        role: str,
        is_active: bool,
    ) -> UserModel:
        user.full_name = full_name.strip()
        user.email = email.strip().lower()
        user.role = role
        user.is_active = is_active

        db.add(user)
        db.commit()
        db.refresh(user)

        return user

    def set_temporary_password(
        self,
        db: Session,
        user: UserModel,
        password_hash: str,
    ) -> None:
        user.password_hash = password_hash
        user.must_change_password = True
        user.password_changed_at = None

        db.add(user)
        db.commit()
        db.refresh(user)

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
        statement = select(
            UserSessionModel
        ).where(
            UserSessionModel.session_token_hash
            == session_token_hash
        )

        return db.scalar(statement)

    def mark_login(
        self,
        db: Session,
        user: UserModel,
    ) -> None:
        user.last_login_at = datetime.now(
            timezone.utc
        )

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
        user.password_changed_at = datetime.now(
            timezone.utc
        )

        db.add(user)
        db.commit()
        db.refresh(user)

    def revoke_session(
        self,
        db: Session,
        session: UserSessionModel,
    ) -> None:
        session.revoked_at = datetime.now(
            timezone.utc
        )

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
                UserSessionModel.user_id
                == user_id,
                UserSessionModel.revoked_at.is_(
                    None
                ),
            )
            .values(
                revoked_at=now,
            )
        )

        db.execute(statement)
        db.commit()


user_repository = UserRepository()
