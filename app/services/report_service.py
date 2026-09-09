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


    def get_audit_activity_report(
        self,
        db: Session,
    ) -> dict:
        summary = (
            report_repository.get_audit_summary(
                db
            )
        )

        rows = (
            report_repository.get_recent_audit_activity(
                db,
                limit=50,
            )
        )

        items = []

        categories = {
            "authentication": 0,
            "assets": 0,
            "monitoring": 0,
            "users": 0,
            "other": 0,
        }

        for row in rows:
            resource_type = (
                row.resource_type or ""
            ).upper()

            if resource_type == "AUTHENTICATION":
                category = "authentication"
            elif resource_type == "ASSET":
                category = "assets"
            elif resource_type in {
                "MONITORING_CONFIG",
                "MONITORING_RESULT",
            }:
                category = "monitoring"
            elif resource_type == "USER":
                category = "users"
            else:
                category = "other"

            categories[category] += 1

            items.append(
                {
                    "id": row.id,
                    "actor_username": (
                        row.actor_username
                        or "System"
                    ),
                    "action": row.action,
                    "resource_type": row.resource_type,
                    "resource_id": row.resource_id,
                    "status": row.status,
                    "ip_address": (
                        row.ip_address
                        or "-"
                    ),
                    "created_at": row.created_at,
                }
            )

        return {
            "summary": summary,
            "items": items,
            "categories": categories,
        }


report_service = ReportService()
