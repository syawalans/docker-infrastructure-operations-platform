from typing import Any

from sqlalchemy.orm import Session

from app.models.audit import AuditLogModel


class AuditRepository:
    def create(
        self,
        db: Session,
        *,
        actor_user_id: int | None,
        actor_username: str | None,
        action: str,
        resource_type: str,
        resource_id: str | None,
        status: str,
        ip_address: str | None,
        details: dict[str, Any] | None,
    ) -> AuditLogModel:
        row = AuditLogModel(
            actor_user_id=actor_user_id,
            actor_username=actor_username,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            status=status,
            ip_address=ip_address,
            details=details,
        )

        db.add(row)
        db.commit()
        db.refresh(row)

        return row


audit_repository = AuditRepository()
