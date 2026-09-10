import platform
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.monitoring import (
    MonitoringConfigModel,
    MonitoringResultModel,
)


class SystemInformationService:
    def get_database_status(
        self,
        db: Session,
    ) -> str:
        try:
            db.execute(text("SELECT 1"))
            return "Healthy"
        except Exception:
            db.rollback()
            return "Unavailable"

    def classify_worker_status(
        self,
        *,
        latest_activity: datetime,
        max_interval_seconds: int,
        now: datetime | None = None,
    ) -> str:
        if latest_activity.tzinfo is None:
            latest_activity = latest_activity.replace(
                tzinfo=timezone.utc
            )

        current_time = (
            now
            if now is not None
            else datetime.now(timezone.utc)
        )

        if current_time.tzinfo is None:
            current_time = current_time.replace(
                tzinfo=timezone.utc
            )

        stale_after_seconds = max(
            max_interval_seconds * 3,
            60,
        )

        stale_after = timedelta(
            seconds=stale_after_seconds
        )

        return (
            "Healthy"
            if current_time - latest_activity
            <= stale_after
            else "Stale"
        )

    def get_worker_information(
        self,
        db: Session,
    ) -> dict:
        enabled_configs = db.execute(
            select(MonitoringConfigModel).where(
                MonitoringConfigModel.enabled.is_(True)
            )
        ).scalars().all()

        if not enabled_configs:
            return {
                "status": "Idle",
                "last_activity": None,
            }

        latest_activity = db.execute(
            select(
                func.max(
                    MonitoringResultModel.checked_at
                )
            )
        ).scalar_one_or_none()

        if latest_activity is None:
            return {
                "status": "Waiting",
                "last_activity": None,
            }

        max_interval = max(
            config.interval_seconds
            for config in enabled_configs
        )

        status = self.classify_worker_status(
            latest_activity=latest_activity,
            max_interval_seconds=max_interval,
        )

        return {
            "status": status,
            "last_activity": latest_activity,
        }

    def get_system_information(
        self,
        db: Session,
    ) -> dict:
        worker = self.get_worker_information(db)

        return {
            "application_version": settings.APP_VERSION,
            "environment": settings.APP_ENV,
            "python_runtime": platform.python_version(),
            "database_status": self.get_database_status(db),
            "worker_status": worker["status"],
            "worker_last_activity": (
                worker["last_activity"]
            ),
        }


system_information_service = (
    SystemInformationService()
)
