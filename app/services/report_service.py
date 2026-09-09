from datetime import datetime, time, timezone

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
        *,
        q: str | None = None,
        asset_type: str | None = None,
        environment: str | None = None,
        status: str | None = None,
        location: str | None = None,
    ) -> dict:
        filters = {
            "q": (q or "").strip(),
            "asset_type": asset_type or "",
            "environment": environment or "",
            "status": status or "",
            "location": location or "",
        }

        query_filters = {
            key: value or None
            for key, value in filters.items()
        }

        return {
            "summary": (
                report_repository.get_asset_summary(
                    db,
                    **query_filters,
                )
            ),
            "assets": (
                report_repository.get_asset_inventory(
                    db,
                    **query_filters,
                )
            ),
            "filter_options": (
                report_repository.get_asset_filter_options(
                    db
                )
            ),
            "filters": filters,
        }


    def get_monitoring_report(
        self,
        db: Session,
        *,
        q: str | None = None,
        status: str | None = None,
        check_type: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> dict:
        filters = {
            "q": (q or "").strip(),
            "status": status or "",
            "check_type": check_type or "",
            "date_from": date_from or "",
            "date_to": date_to or "",
        }

        parsed_date_from = None
        parsed_date_to = None

        if filters["date_from"]:
            try:
                parsed_date_from = datetime.combine(
                    datetime.strptime(
                        filters["date_from"],
                        "%Y-%m-%d",
                    ).date(),
                    time.min,
                    tzinfo=timezone.utc,
                )
            except ValueError:
                filters["date_from"] = ""

        if filters["date_to"]:
            try:
                parsed_date_to = datetime.combine(
                    datetime.strptime(
                        filters["date_to"],
                        "%Y-%m-%d",
                    ).date(),
                    time.max,
                    tzinfo=timezone.utc,
                )
            except ValueError:
                filters["date_to"] = ""

        rows = (
            report_repository.get_monitoring_report(
                db,
                q=filters["q"] or None,
                status=filters["status"] or None,
                check_type=(
                    filters["check_type"] or None
                ),
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
                db,
                q=filters["q"] or None,
                status=filters["status"] or None,
                check_type=(
                    filters["check_type"] or None
                ),
                date_from=parsed_date_from,
                date_to=parsed_date_to,
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
                q=filters["q"] or None,
                status=filters["status"] or None,
                check_type=(
                    filters["check_type"] or None
                ),
                date_from=parsed_date_from,
                date_to=parsed_date_to,
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
            "filters": filters,
            "filter_options": (
                report_repository.get_monitoring_filter_options(
                    db
                )
            ),
        }


    def get_audit_activity_report(
        self,
        db: Session,
        *,
        actor: str | None = None,
        action: str | None = None,
        resource_type: str | None = None,
        status: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> dict:
        filters = {
            "actor": (actor or "").strip(),
            "action": action or "",
            "resource_type": resource_type or "",
            "status": status or "",
            "date_from": date_from or "",
            "date_to": date_to or "",
        }

        parsed_date_from = None
        parsed_date_to = None

        if filters["date_from"]:
            try:
                parsed_date_from = datetime.combine(
                    datetime.strptime(
                        filters["date_from"],
                        "%Y-%m-%d",
                    ).date(),
                    time.min,
                    tzinfo=timezone.utc,
                )
            except ValueError:
                filters["date_from"] = ""

        if filters["date_to"]:
            try:
                parsed_date_to = datetime.combine(
                    datetime.strptime(
                        filters["date_to"],
                        "%Y-%m-%d",
                    ).date(),
                    time.max,
                    tzinfo=timezone.utc,
                )
            except ValueError:
                filters["date_to"] = ""

        query_filters = {
            "actor": filters["actor"] or None,
            "action": filters["action"] or None,
            "resource_type": (
                filters["resource_type"] or None
            ),
            "status": filters["status"] or None,
            "date_from": parsed_date_from,
            "date_to": parsed_date_to,
        }

        summary = (
            report_repository.get_audit_summary(
                db,
                **query_filters,
            )
        )

        categories = (
            report_repository.get_audit_breakdown(
                db,
                **query_filters,
            )
        )

        rows = (
            report_repository.get_recent_audit_activity(
                db,
                **query_filters,
                limit=50,
            )
        )

        items = []

        for row in rows:
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
            "filters": filters,
            "filter_options": (
                report_repository.get_audit_filter_options(
                    db
                )
            ),
        }


report_service = ReportService()
