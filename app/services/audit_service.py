from typing import Any

from fastapi import Request
from sqlalchemy.orm import Session

from app.models.audit import AuditLogModel
from app.models.user import UserModel
from app.repositories.audit_repository import (
    audit_repository,
)


SENSITIVE_DETAIL_KEYS = {
    "password",
    "password_hash",
    "temporary_password",
    "session_token",
    "session_token_hash",
    "csrf_token",
    "cookie",
    "secret",
}


class AuditService:
    @staticmethod
    def get_client_ip(
        request: Request,
    ) -> str | None:
        if request.client is None:
            return None

        return request.client.host

    def _sanitize_value(
        self,
        value: Any,
    ) -> Any:
        if isinstance(value, dict):
            sanitized = {}

            for key, item in value.items():
                if (
                    str(key).lower()
                    in SENSITIVE_DETAIL_KEYS
                ):
                    continue

                sanitized[key] = (
                    self._sanitize_value(item)
                )

            return sanitized

        if isinstance(value, list):
            return [
                self._sanitize_value(item)
                for item in value
            ]

        if isinstance(value, tuple):
            return [
                self._sanitize_value(item)
                for item in value
            ]

        return value

    def sanitize_details(
        self,
        details: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        if details is None:
            return None

        sanitized = self._sanitize_value(
            details
        )

        return sanitized or None

    def log(
        self,
        db: Session,
        *,
        action: str,
        resource_type: str,
        status: str,
        actor: UserModel | None = None,
        actor_username: str | None = None,
        resource_id: str | int | None = None,
        request: Request | None = None,
        details: dict[str, Any] | None = None,
    ) -> AuditLogModel:
        resolved_username = (
            actor.username
            if actor is not None
            else actor_username
        )

        resolved_user_id = (
            actor.id
            if actor is not None
            else None
        )

        ip_address = (
            self.get_client_ip(request)
            if request is not None
            else None
        )

        return audit_repository.create(
            db,
            actor_user_id=resolved_user_id,
            actor_username=resolved_username,
            action=action,
            resource_type=resource_type,
            resource_id=(
                str(resource_id)
                if resource_id is not None
                else None
            ),
            status=status,
            ip_address=ip_address,
            details=self.sanitize_details(
                details
            ),
        )


audit_service = AuditService()
