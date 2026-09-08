from sqlalchemy.orm import Session

from app.repositories.report_repository import (
    report_repository,
)


class ReportService:
    def get_overview(
        self,
        db: Session,
    ) -> dict:
        return {
            "asset_summary": (
                report_repository.get_asset_summary(
                    db
                )
            ),
        }

    def get_asset_inventory_report(
        self,
        db: Session,
    ) -> dict:
        return {
            "summary": (
                report_repository.get_asset_summary(
                    db
                )
            ),
            "assets": (
                report_repository.get_asset_inventory(
                    db
                )
            ),
        }


    def get_monitoring_report(
        self,
        db: Session,
    ) -> dict:
        rows = (
            report_repository.get_monitoring_report(
                db
            )
        )

        items = []

        for row in rows:
            asset = row["asset"]
            config = row["config"]
            result = row["latest_result"]

            status = (
                result.status
                if result is not None
                else "UNKNOWN"
            )

            items.append(
                {
                    "asset_id": asset.id,
                    "hostname": asset.hostname,
                    "asset_type": asset.asset_type,
                    "environment": asset.environment,
                    "check_type": config.check_type,
                    "target": config.target,
                    "port": config.port,
                    "http_path": config.http_path,
                    "status": status,
                    "response_time_ms": (
                        result.response_time_ms
                        if result is not None
                        else None
                    ),
                    "checked_at": (
                        result.checked_at
                        if result is not None
                        else None
                    ),
                }
            )

        stats = {
            "total_monitored": len(items),
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

        history_summary = (
            report_repository.get_monitoring_history_summary(
                db
            )
        )

        total_checks = history_summary[
            "total_checks"
        ]

        successful_checks = history_summary[
            "successful_checks"
        ]

        availability_percent = (
            successful_checks
            / total_checks
            * 100
            if total_checks > 0
            else 0.0
        )

        recent_rows = (
            report_repository.get_recent_monitoring_history(
                db,
                limit=20,
            )
        )

        history_items = []

        for row in recent_rows:
            asset = row["asset"]
            result = row["result"]

            history_items.append(
                {
                    "hostname": asset.hostname,
                    "asset_id": asset.id,
                    "check_type": result.check_type,
                    "target": result.target,
                    "port": result.port,
                    "http_path": result.http_path,
                    "status": result.status,
                    "response_time_ms": (
                        result.response_time_ms
                    ),
                    "checked_at": result.checked_at,
                }
            )

        performance = {
            **history_summary,
            "availability_percent": (
                availability_percent
            ),
        }

        return {
            "stats": stats,
            "items": items,
            "performance": performance,
            "history_items": history_items,
        }


report_service = ReportService()
