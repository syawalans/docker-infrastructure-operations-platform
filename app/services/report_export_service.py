import csv
from datetime import datetime, timezone
from io import StringIO

from sqlalchemy.orm import Session

from app.repositories.report_repository import (
    report_repository,
)
from app.services.report_service import report_service
from app.services.report_date_service import report_date_service


CSV_FORMULA_PREFIXES = (
    "=",
    "+",
    "-",
    "@",
)


class ReportExportService:
    @staticmethod
    def _safe_csv_value(
        value,
    ) -> str:
        if value is None:
            return ""

        text = str(value)

        if text.startswith(
            CSV_FORMULA_PREFIXES
        ):
            return "'" + text

        return text

    def export_asset_inventory_csv(
        self,
        db: Session,
        *,
        q: str | None = None,
        asset_type: str | None = None,
        environment: str | None = None,
        status: str | None = None,
        location: str | None = None,
    ) -> tuple[bytes, str]:
        data = (
            report_service.get_asset_inventory_report(
                db,
                q=q,
                asset_type=asset_type,
                environment=environment,
                status=status,
                location=location,
            )
        )

        output = StringIO(
            newline=""
        )

        writer = csv.writer(output)

        writer.writerow(
            [
                "Hostname",
                "Name",
                "Asset Type",
                "IP Address",
                "Vendor",
                "Model",
                "Operating System",
                "Environment",
                "Location",
                "Status",
            ]
        )

        for asset in data["assets"]:
            writer.writerow(
                [
                    self._safe_csv_value(
                        asset.hostname
                    ),
                    self._safe_csv_value(
                        asset.name
                    ),
                    self._safe_csv_value(
                        asset.asset_type
                    ),
                    self._safe_csv_value(
                        asset.ip_address
                    ),
                    self._safe_csv_value(
                        asset.vendor
                    ),
                    self._safe_csv_value(
                        asset.model
                    ),
                    self._safe_csv_value(
                        asset.operating_system
                    ),
                    self._safe_csv_value(
                        asset.environment
                    ),
                    self._safe_csv_value(
                        asset.location
                    ),
                    self._safe_csv_value(
                        asset.status
                    ),
                ]
            )

        generated_date = (
            datetime.now(
                timezone.utc
            ).strftime(
                "%Y-%m-%d"
            )
        )

        filename = (
            "Asset_Inventory_"
            f"{generated_date}.csv"
        )

        content = (
            "\ufeff"
            + output.getvalue()
        ).encode(
            "utf-8"
        )

        return content, filename


    def export_monitoring_csv(
        self,
        db: Session,
        *,
        q: str | None = None,
        status: str | None = None,
        check_type: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> tuple[bytes, str]:
        data = report_service.get_monitoring_report(
            db,
            q=q,
            status=status,
            check_type=check_type,
            date_from=date_from,
            date_to=date_to,
        )

        filters = data["filters"]

        date_range = report_date_service.require_valid(
            filters["date_from"],
            filters["date_to"],
        )

        parsed_date_from = (
            date_range.parsed_date_from
        )
        parsed_date_to = (
            date_range.parsed_date_to
        )

        rows = (
            report_repository
            .get_recent_monitoring_history(
                db,
                q=filters["q"] or None,
                status=filters["status"] or None,
                check_type=(
                    filters["check_type"] or None
                ),
                date_from=parsed_date_from,
                date_to=parsed_date_to,
                limit=None,
            )
        )

        output = StringIO(
            newline=""
        )

        writer = csv.writer(output)

        writer.writerow(
            [
                "Asset",
                "Check Type",
                "Target",
                "Port",
                "HTTP Path",
                "Status",
                "Response Time (ms)",
                "Checked At (UTC)",
            ]
        )

        for row in rows:
            asset = row["asset"]
            result = row["result"]

            writer.writerow(
                [
                    self._safe_csv_value(
                        asset.hostname
                    ),
                    self._safe_csv_value(
                        result.check_type
                    ),
                    self._safe_csv_value(
                        result.target
                    ),
                    self._safe_csv_value(
                        result.port
                    ),
                    self._safe_csv_value(
                        result.http_path
                    ),
                    self._safe_csv_value(
                        result.status
                    ),
                    self._safe_csv_value(
                        result.response_time_ms
                    ),
                    self._safe_csv_value(
                        result.checked_at.isoformat()
                    ),
                ]
            )

        generated_date = datetime.now(
            timezone.utc
        ).strftime(
            "%Y-%m-%d"
        )

        filename = (
            "Monitoring_Report_"
            f"{generated_date}.csv"
        )

        content = (
            "\ufeff"
            + output.getvalue()
        ).encode(
            "utf-8"
        )

        return content, filename


    def export_audit_activity_csv(
        self,
        db: Session,
        *,
        actor: str | None = None,
        action: str | None = None,
        resource_type: str | None = None,
        status: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> tuple[bytes, str]:
        data = (
            report_service.get_audit_activity_report(
                db,
                actor=actor,
                action=action,
                resource_type=resource_type,
                status=status,
                date_from=date_from,
                date_to=date_to,
            )
        )

        filters = data["filters"]

        date_range = report_date_service.require_valid(
            filters["date_from"],
            filters["date_to"],
        )

        parsed_date_from = (
            date_range.parsed_date_from
        )
        parsed_date_to = (
            date_range.parsed_date_to
        )

        rows = (
            report_repository
            .get_recent_audit_activity(
                db,
                actor=filters["actor"] or None,
                action=filters["action"] or None,
                resource_type=(
                    filters["resource_type"]
                    or None
                ),
                status=filters["status"] or None,
                date_from=parsed_date_from,
                date_to=parsed_date_to,
                limit=None,
            )
        )

        output = StringIO(
            newline=""
        )

        writer = csv.writer(output)

        writer.writerow(
            [
                "Event ID",
                "Actor",
                "Action",
                "Resource Type",
                "Resource ID",
                "Status",
                "IP Address",
                "Created At (UTC)",
            ]
        )

        for row in rows:
            writer.writerow(
                [
                    self._safe_csv_value(
                        row.id
                    ),
                    self._safe_csv_value(
                        row.actor_username
                        or "System"
                    ),
                    self._safe_csv_value(
                        row.action
                    ),
                    self._safe_csv_value(
                        row.resource_type
                    ),
                    self._safe_csv_value(
                        row.resource_id
                    ),
                    self._safe_csv_value(
                        row.status
                    ),
                    self._safe_csv_value(
                        row.ip_address
                    ),
                    self._safe_csv_value(
                        row.created_at.isoformat()
                    ),
                ]
            )

        generated_date = datetime.now(
            timezone.utc
        ).strftime(
            "%Y-%m-%d"
        )

        filename = (
            "Audit_Activity_"
            f"{generated_date}.csv"
        )

        content = (
            "\ufeff"
            + output.getvalue()
        ).encode(
            "utf-8"
        )

        return content, filename


report_export_service = ReportExportService()
