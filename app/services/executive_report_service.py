from collections import Counter
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.services.report_service import report_service


class ExecutiveReportService:
    def get_executive_report(
        self,
        db: Session,
        *,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> dict:
        assets = report_service.get_asset_inventory_report(db)

        monitoring = report_service.get_monitoring_report(
            db,
            date_from=date_from,
            date_to=date_to,
        )

        audit = report_service.get_audit_activity_report(
            db,
            date_from=date_from,
            date_to=date_to,
        )

        generated_at = datetime.now(timezone.utc)

        asset_summary = assets["summary"]
        asset_items = assets["assets"]

        monitoring_stats = monitoring["stats"]
        monitoring_items = monitoring["items"]
        performance = monitoring["performance"]

        audit_summary = audit["summary"]
        audit_categories = audit["categories"]

        asset_distribution = self._build_asset_distribution(
            asset_items
        )

        affected_assets = self._build_affected_assets(
            asset_items=asset_items,
            monitoring_items=monitoring_items,
        )

        findings = self._build_findings(
            asset_summary=asset_summary,
            monitoring_stats=monitoring_stats,
            performance=performance,
            audit_summary=audit_summary,
            affected_assets=affected_assets,
        )

        overall_status = self._determine_overall_status(
            asset_summary=asset_summary,
            monitoring_stats=monitoring_stats,
            audit_summary=audit_summary,
        )

        management_summary = self._build_management_summary(
            overall_status=overall_status,
            asset_summary=asset_summary,
            monitoring_stats=monitoring_stats,
            performance=performance,
            audit_summary=audit_summary,
        )

        return {
            "generated_at": generated_at,
            "reporting_period": {
                "date_from": date_from,
                "date_to": date_to,
            },
            "overall_status": overall_status,
            "executive_summary": {
                "total_assets": asset_summary["total_assets"],
                "active_assets": asset_summary["active_assets"],
                "maintenance_assets": (
                    asset_summary["maintenance_assets"]
                ),
                "inactive_assets": (
                    asset_summary["inactive_assets"]
                ),
                "total_monitored": (
                    monitoring_stats["total_monitored"]
                ),
                "monitoring_up": monitoring_stats["up"],
                "monitoring_down": monitoring_stats["down"],
                "monitoring_unknown": (
                    monitoring_stats["unknown"]
                ),
                "availability_percent": (
                    performance["availability_percent"]
                ),
                "total_monitoring_checks": (
                    performance["total_checks"]
                ),
                "successful_monitoring_checks": (
                    performance["successful_checks"]
                ),
                "failed_monitoring_checks": (
                    performance["failed_checks"]
                ),
                "average_response_time_ms": (
                    performance["average_response_time_ms"]
                ),
                "total_audit_events": (
                    audit_summary["total_events"]
                ),
                "successful_audit_events": (
                    audit_summary["success_events"]
                ),
                "failed_audit_events": (
                    audit_summary["failure_events"]
                ),
                "blocked_audit_events": (
                    audit_summary["blocked_events"]
                ),
            },
            "asset_overview": {
                "summary": asset_summary,
                "distribution": asset_distribution,
                "assets": asset_items,
            },
            "affected_assets": affected_assets,
            "monitoring_overview": {
                "stats": monitoring_stats,
                "performance": performance,
                "current_items": monitoring_items,
                "history_items": monitoring["history_items"],
            },
            "audit_overview": {
                "summary": audit_summary,
                "categories": audit_categories,
                "items": audit["items"],
            },
            "findings": findings,
            "management_summary": management_summary,
        }

    @staticmethod
    def _build_asset_distribution(
        assets: list,
    ) -> dict:
        def count_by(field: str) -> list[dict]:
            values = Counter(
                (
                    getattr(asset, field, None)
                    or "Unspecified"
                )
                for asset in assets
            )

            return [
                {
                    "label": label,
                    "count": count,
                }
                for label, count in sorted(
                    values.items(),
                    key=lambda item: (
                        -item[1],
                        item[0],
                    ),
                )
            ]

        return {
            "asset_type": count_by("asset_type"),
            "environment": count_by("environment"),
            "status": count_by("status"),
            "location": count_by("location"),
        }

    @staticmethod
    def _serialize_asset(asset) -> dict:
        return {
            "id": asset.id,
            "hostname": asset.hostname,
            "name": asset.name,
            "asset_type": asset.asset_type,
            "ip_address": asset.ip_address,
            "vendor": asset.vendor,
            "model": asset.model,
            "operating_system": asset.operating_system,
            "environment": asset.environment,
            "location": asset.location,
            "status": asset.status,
        }

    def _build_affected_assets(
        self,
        *,
        asset_items: list,
        monitoring_items: list[dict],
    ) -> dict:
        maintenance = []
        inactive = []

        for asset in asset_items:
            status = (asset.status or "").upper()

            serialized = self._serialize_asset(asset)

            if status == "MAINTENANCE":
                maintenance.append(serialized)

            if status == "INACTIVE":
                inactive.append(serialized)

        monitoring_down = []
        monitoring_unknown = []

        for item in monitoring_items:
            current = {
                "asset_id": item.get("asset_id"),
                "hostname": item.get("hostname"),
                "asset_type": item.get("asset_type"),
                "environment": item.get("environment"),
                "status": item.get("status"),
                "target": item.get("target"),
                "port": item.get("port"),
                "check_type": item.get("check_type"),
                "checked_at": item.get("checked_at"),
            }

            status = (
                item.get("status") or "UNKNOWN"
            ).upper()

            if status == "DOWN":
                monitoring_down.append(current)

            if status == "UNKNOWN":
                monitoring_unknown.append(current)

        return {
            "maintenance": maintenance,
            "inactive": inactive,
            "monitoring_down": monitoring_down,
            "monitoring_unknown": monitoring_unknown,
        }

    @staticmethod
    def _determine_overall_status(
        *,
        asset_summary: dict,
        monitoring_stats: dict,
        audit_summary: dict,
    ) -> str:
        if (
            monitoring_stats["down"] > 0
            or asset_summary["inactive_assets"] > 0
        ):
            return "ATTENTION"

        if (
            monitoring_stats["unknown"] > 0
            or asset_summary["maintenance_assets"] > 0
            or audit_summary["blocked_events"] > 0
        ):
            return "REVIEW"

        return "HEALTHY"

    @staticmethod
    def _build_findings(
        *,
        asset_summary: dict,
        monitoring_stats: dict,
        performance: dict,
        audit_summary: dict,
        affected_assets: dict,
    ) -> list[dict]:
        findings: list[dict] = []

        if asset_summary["inactive_assets"] > 0:
            findings.append(
                {
                    "severity": "HIGH",
                    "category": "ASSETS",
                    "title": (
                        "Inactive infrastructure "
                        "assets detected"
                    ),
                    "value": (
                        asset_summary["inactive_assets"]
                    ),
                    "affected_assets": (
                        affected_assets["inactive"]
                    ),
                    "scope": "CURRENT",
                }
            )

        if asset_summary["maintenance_assets"] > 0:
            findings.append(
                {
                    "severity": "MEDIUM",
                    "category": "ASSETS",
                    "title": (
                        "Infrastructure assets "
                        "currently under maintenance"
                    ),
                    "value": (
                        asset_summary[
                            "maintenance_assets"
                        ]
                    ),
                    "affected_assets": (
                        affected_assets["maintenance"]
                    ),
                    "scope": "CURRENT",
                }
            )

        if monitoring_stats["down"] > 0:
            findings.append(
                {
                    "severity": "HIGH",
                    "category": "MONITORING",
                    "title": (
                        "Monitored infrastructure "
                        "currently unavailable"
                    ),
                    "value": monitoring_stats["down"],
                    "affected_assets": (
                        affected_assets[
                            "monitoring_down"
                        ]
                    ),
                    "scope": "CURRENT",
                }
            )

        if monitoring_stats["unknown"] > 0:
            findings.append(
                {
                    "severity": "MEDIUM",
                    "category": "MONITORING",
                    "title": (
                        "Monitoring status could "
                        "not be determined"
                    ),
                    "value": monitoring_stats["unknown"],
                    "affected_assets": (
                        affected_assets[
                            "monitoring_unknown"
                        ]
                    ),
                    "scope": "CURRENT",
                }
            )

        if performance["failed_checks"] > 0:
            findings.append(
                {
                    "severity": "MEDIUM",
                    "category": "MONITORING",
                    "title": (
                        "Monitoring failures occurred "
                        "during the reporting period"
                    ),
                    "value": performance["failed_checks"],
                    "affected_assets": [],
                    "scope": "HISTORICAL",
                }
            )

        if audit_summary["failure_events"] > 0:
            findings.append(
                {
                    "severity": "MEDIUM",
                    "category": "AUDIT",
                    "title": (
                        "Failed operational or "
                        "authentication events detected"
                    ),
                    "value": (
                        audit_summary["failure_events"]
                    ),
                    "affected_assets": [],
                    "scope": "HISTORICAL",
                }
            )

        if audit_summary["blocked_events"] > 0:
            findings.append(
                {
                    "severity": "MEDIUM",
                    "category": "SECURITY",
                    "title": (
                        "Blocked security events "
                        "detected"
                    ),
                    "value": (
                        audit_summary["blocked_events"]
                    ),
                    "affected_assets": [],
                    "scope": "HISTORICAL",
                }
            )

        if not findings:
            findings.append(
                {
                    "severity": "INFO",
                    "category": "OPERATIONS",
                    "title": (
                        "No significant operational "
                        "exceptions detected"
                    ),
                    "value": 0,
                    "affected_assets": [],
                    "scope": "CURRENT",
                }
            )

        return findings

    @staticmethod
    def _build_management_summary(
        *,
        overall_status: str,
        asset_summary: dict,
        monitoring_stats: dict,
        performance: dict,
        audit_summary: dict,
    ) -> dict:
        attention_items = []

        if monitoring_stats["down"] > 0:
            attention_items.append(
                (
                    f'{monitoring_stats["down"]} monitored '
                    "asset(s) currently DOWN"
                )
            )

        if monitoring_stats["unknown"] > 0:
            attention_items.append(
                (
                    f'{monitoring_stats["unknown"]} '
                    "monitoring status(es) UNKNOWN"
                )
            )

        if asset_summary["inactive_assets"] > 0:
            attention_items.append(
                (
                    f'{asset_summary["inactive_assets"]} '
                    "inactive asset(s)"
                )
            )

        if asset_summary["maintenance_assets"] > 0:
            attention_items.append(
                (
                    f'{asset_summary["maintenance_assets"]} '
                    "asset(s) under maintenance"
                )
            )

        if performance["failed_checks"] > 0:
            attention_items.append(
                (
                    (
                    f'{performance["failed_checks"]} '
                    + (
                        "monitoring failure"
                        if performance["failed_checks"] == 1
                        else "monitoring failures"
                    )
                    + " recorded during the reporting period"
                )
                )
            )

        if audit_summary["failure_events"] > 0:
            attention_items.append(
                (
                    (
                    f'{audit_summary["failure_events"]} '
                    + (
                        "failed audit event"
                        if audit_summary["failure_events"] == 1
                        else "failed audit events"
                    )
                    + " recorded"
                )
                )
            )

        if audit_summary["blocked_events"] > 0:
            attention_items.append(
                (
                    (
                    f'{audit_summary["blocked_events"]} '
                    + (
                        "blocked security event"
                        if audit_summary["blocked_events"] == 1
                        else "blocked security events"
                    )
                    + " recorded"
                )
                )
            )

        if not attention_items:
            attention_items.append(
                (
                    "No significant operational "
                    "exceptions require attention."
                )
            )

        if overall_status == "HEALTHY":
            statement = (
                "Current infrastructure services are "
                "operational with no significant "
                "exceptions detected."
            )

        elif overall_status == "REVIEW":
            statement = (
                "Current infrastructure services are "
                "operational, but historical or "
                "non-critical conditions require "
                "management review."
            )

        else:
            statement = (
                "One or more current infrastructure "
                "conditions require management "
                "attention."
            )

        return {
            "status": overall_status,
            "statement": statement,
            "attention_items": attention_items,
        }


executive_report_service = ExecutiveReportService()
