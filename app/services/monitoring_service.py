from sqlalchemy.orm import Session

from app.repositories.monitoring_repository import monitoring_repository


class MonitoringService:
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
