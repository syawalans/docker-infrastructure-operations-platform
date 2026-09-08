from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.constants import MONITORING_CHECK_TYPES
from app.repositories.monitoring_repository import monitoring_repository
from app.schemas.monitoring import MonitoringConfigCreate
from app.services.monitoring_checker import monitoring_checker


class MonitoringService:
    def get_config_by_asset(
        self,
        db: Session,
        asset_id: int,
    ):
        return monitoring_repository.get_config_by_asset(
            db,
            asset_id,
        )

    def save_config(
        self,
        db: Session,
        data: MonitoringConfigCreate,
    ):
        check_type = data.check_type.upper()

        if check_type not in MONITORING_CHECK_TYPES:
            raise ValueError(
                "Unsupported monitoring check type."
            )

        if check_type == "TCP" and data.port is None:
            raise ValueError(
                "TCP monitoring requires a port."
            )

        if check_type == "HTTP" and data.port is None:
            data.port = 80

        if check_type == "HTTPS" and data.port is None:
            data.port = 443

        if check_type == "ICMP":
            data.port = None
            data.http_path = None

        if check_type == "TCP":
            data.http_path = None

        data.check_type = check_type

        existing = monitoring_repository.get_config_by_asset(
            db,
            data.asset_id,
        )

        if existing is None:
            return monitoring_repository.create_config(
                db,
                data,
            )

        return monitoring_repository.update_config(
            db,
            existing,
            data,
        )

    def delete_config(
        self,
        db: Session,
        asset_id: int,
    ) -> bool:
        config = monitoring_repository.get_config_by_asset(
            db,
            asset_id,
        )

        if config is None:
            return False

        monitoring_repository.delete_config(
            db,
            config,
        )

        return True

    def run_check(
        self,
        db: Session,
        asset_id: int,
    ):
        config = monitoring_repository.get_config_by_asset(
            db,
            asset_id,
        )

        if config is None:
            raise ValueError(
                "Monitoring is not configured for this asset."
            )

        if not config.enabled:
            raise ValueError(
                "Monitoring is disabled for this asset."
            )

        return self.run_config_check(
            db,
            config,
        )

    def run_config_check(
        self,
        db: Session,
        config,
    ):
        check_result = monitoring_checker.run(
            check_type=config.check_type,
            target=config.target,
            port=config.port,
            http_path=config.http_path,
            timeout_seconds=config.timeout_seconds,
        )

        return monitoring_repository.create_result(
            db,
            asset_id=config.asset_id,
            config_id=config.id,
            check_type=config.check_type,
            target=config.target,
            port=config.port,
            http_path=config.http_path,
            status=check_result.status,
            response_time_ms=check_result.response_time_ms,
            error_message=check_result.error_message,
        )

    def is_check_due(
        self,
        db: Session,
        config,
        now: datetime | None = None,
    ) -> bool:
        latest_result = (
            monitoring_repository.get_latest_result_by_config(
                db,
                config.id,
            )
        )

        if latest_result is None:
            return True

        current_time = now or datetime.now(
            timezone.utc
        )

        next_check_at = (
            latest_result.checked_at
            + timedelta(
                seconds=config.interval_seconds
            )
        )

        return current_time >= next_check_at

    def run_due_checks(
        self,
        db: Session,
    ) -> dict:
        configs = (
            monitoring_repository.get_enabled_configs(
                db
            )
        )

        checked = 0
        skipped = 0
        failed = 0

        now = datetime.now(
            timezone.utc
        )

        for config in configs:
            if not self.is_check_due(
                db,
                config,
                now,
            ):
                skipped += 1
                continue

            try:
                self.run_config_check(
                    db,
                    config,
                )

                checked += 1

            except Exception:
                db.rollback()
                failed += 1

        return {
            "checked": checked,
            "skipped": skipped,
            "failed": failed,
        }

    def get_overview(
        self,
        db: Session,
    ) -> dict:
        rows = monitoring_repository.get_overview(db)

        items = []

        for row in rows:
            asset = row["asset"]
            config = row["config"]
            result = row["latest_result"]

            if config is None:
                status = "UNKNOWN"
                check_type = "Not Configured"
                response_time_ms = None
                checked_at = None
            elif result is None:
                status = "UNKNOWN"
                check_type = config.check_type
                response_time_ms = None
                checked_at = None
            else:
                status = result.status
                check_type = config.check_type
                response_time_ms = result.response_time_ms
                checked_at = result.checked_at

            items.append(
                {
                    "asset_id": asset.id,
                    "hostname": asset.hostname,
                    "asset_type": asset.asset_type,
                    "ip_address": asset.ip_address,
                    "environment": asset.environment,
                    "check_type": check_type,
                    "status": status,
                    "response_time_ms": response_time_ms,
                    "checked_at": checked_at,
                    "configured": config is not None,
                }
            )

        stats = {
            "total_monitored": sum(
                1
                for item in items
                if item["configured"]
            ),
            "up": sum(
                1
                for item in items
                if item["status"] == "UP"
            ),
            "down": sum(
                1
                for item in items
                if item["status"] == "DOWN"
            ),
            "unknown": sum(
                1
                for item in items
                if item["status"] == "UNKNOWN"
            ),
        }

        return {
            "stats": stats,
            "items": items,
        }


monitoring_service = MonitoringService()
