from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.asset import AssetModel
from app.models.audit import AuditLogModel
from app.models.monitoring import (
    MonitoringConfigModel,
    MonitoringResultModel,
)


class ReportRepository:
    def _apply_asset_filters(
        self,
        statement,
        *,
        q: str | None = None,
        asset_type: str | None = None,
        environment: str | None = None,
        status: str | None = None,
        location: str | None = None,
    ):
        if q:
            search = f"%{q.strip()}%"

            statement = statement.where(
                or_(
                    AssetModel.hostname.ilike(search),
                    AssetModel.name.ilike(search),
                    AssetModel.ip_address.ilike(search),
                    AssetModel.vendor.ilike(search),
                    AssetModel.model.ilike(search),
                )
            )

        if asset_type:
            statement = statement.where(
                AssetModel.asset_type == asset_type
            )

        if environment:
            statement = statement.where(
                AssetModel.environment == environment
            )

        if status:
            statement = statement.where(
                AssetModel.status == status
            )

        if location:
            statement = statement.where(
                AssetModel.location == location
            )

        return statement

    def get_asset_inventory(
        self,
        db: Session,
        *,
        q: str | None = None,
        asset_type: str | None = None,
        environment: str | None = None,
        status: str | None = None,
        location: str | None = None,
    ) -> list[AssetModel]:
        statement = self._apply_asset_filters(
            select(AssetModel),
            q=q,
            asset_type=asset_type,
            environment=environment,
            status=status,
            location=location,
        ).order_by(
            AssetModel.hostname.asc()
        )

        return list(
            db.execute(
                statement
            ).scalars().all()
        )

    def get_asset_summary(
        self,
        db: Session,
        *,
        q: str | None = None,
        asset_type: str | None = None,
        environment: str | None = None,
        status: str | None = None,
        location: str | None = None,
    ) -> dict[str, int]:
        base_statement = self._apply_asset_filters(
            select(AssetModel.id),
            q=q,
            asset_type=asset_type,
            environment=environment,
            status=status,
            location=location,
        )

        filtered_ids = base_statement.subquery()

        total_assets = db.scalar(
            select(
                func.count()
            ).select_from(filtered_ids)
        ) or 0

        active_assets = db.scalar(
            select(
                func.count()
            ).select_from(
                self._apply_asset_filters(
                    select(AssetModel.id),
                    q=q,
                    asset_type=asset_type,
                    environment=environment,
                    status=status,
                    location=location,
                ).where(
                    AssetModel.status == "Active"
                ).subquery()
            )
        ) or 0

        maintenance_assets = db.scalar(
            select(
                func.count()
            ).select_from(
                self._apply_asset_filters(
                    select(AssetModel.id),
                    q=q,
                    asset_type=asset_type,
                    environment=environment,
                    status=status,
                    location=location,
                ).where(
                    AssetModel.status == "Maintenance"
                ).subquery()
            )
        ) or 0

        inactive_assets = db.scalar(
            select(
                func.count()
            ).select_from(
                self._apply_asset_filters(
                    select(AssetModel.id),
                    q=q,
                    asset_type=asset_type,
                    environment=environment,
                    status=status,
                    location=location,
                ).where(
                    AssetModel.status == "Inactive"
                ).subquery()
            )
        ) or 0

        return {
            "total_assets": total_assets,
            "active_assets": active_assets,
            "maintenance_assets": maintenance_assets,
            "inactive_assets": inactive_assets,
        }

    def get_asset_filter_options(
        self,
        db: Session,
    ) -> dict[str, list[str]]:
        def distinct_values(column):
            return list(
                db.execute(
                    select(column)
                    .where(
                        column.is_not(None)
                    )
                    .distinct()
                    .order_by(column.asc())
                ).scalars().all()
            )

        return {
            "asset_types": distinct_values(
                AssetModel.asset_type
            ),
            "environments": distinct_values(
                AssetModel.environment
            ),
            "statuses": distinct_values(
                AssetModel.status
            ),
            "locations": distinct_values(
                AssetModel.location
            ),
        }


    def get_monitoring_report(
        self,
        db: Session,
        *,
        q: str | None = None,
        status: str | None = None,
        check_type: str | None = None,
    ) -> list[dict]:
        statement = (
            select(MonitoringConfigModel)
            .where(
                MonitoringConfigModel.enabled.is_(True)
            )
            .order_by(
                MonitoringConfigModel.asset_id.asc()
            )
        )

        if check_type:
            statement = statement.where(
                MonitoringConfigModel.check_type
                == check_type
            )

        configs = list(
            db.execute(
                statement
            ).scalars().all()
        )

        rows = []

        for config in configs:
            asset = db.get(
                AssetModel,
                config.asset_id,
            )

            if asset is None:
                continue

            if q:
                search = q.strip().lower()

                searchable = " ".join(
                    [
                        asset.hostname or "",
                        asset.name or "",
                        asset.ip_address or "",
                        config.target or "",
                    ]
                ).lower()

                if search not in searchable:
                    continue

            latest_result = db.execute(
                select(MonitoringResultModel)
                .where(
                    MonitoringResultModel.config_id
                    == config.id
                )
                .order_by(
                    MonitoringResultModel.checked_at.desc(),
                    MonitoringResultModel.id.desc(),
                )
                .limit(1)
            ).scalar_one_or_none()

            current_status = (
                latest_result.status
                if latest_result is not None
                else "UNKNOWN"
            )

            if (
                status
                and current_status != status
            ):
                continue

            rows.append(
                {
                    "asset": asset,
                    "config": config,
                    "latest_result": latest_result,
                }
            )

        return rows

    def _apply_monitoring_history_filters(
        self,
        statement,
        *,
        q: str | None = None,
        status: str | None = None,
        check_type: str | None = None,
        date_from=None,
        date_to=None,
    ):
        if q:
            search = f"%{q.strip()}%"

            statement = statement.where(
                or_(
                    AssetModel.hostname.ilike(search),
                    AssetModel.name.ilike(search),
                    AssetModel.ip_address.ilike(search),
                    MonitoringResultModel.target.ilike(
                        search
                    ),
                )
            )

        if status:
            statement = statement.where(
                MonitoringResultModel.status
                == status
            )

        if check_type:
            statement = statement.where(
                MonitoringResultModel.check_type
                == check_type
            )

        if date_from is not None:
            statement = statement.where(
                MonitoringResultModel.checked_at
                >= date_from
            )

        if date_to is not None:
            statement = statement.where(
                MonitoringResultModel.checked_at
                <= date_to
            )

        return statement

    def get_monitoring_history_summary(
        self,
        db: Session,
        *,
        q: str | None = None,
        status: str | None = None,
        check_type: str | None = None,
        date_from=None,
        date_to=None,
    ) -> dict:
        def filtered_statement():
            statement = (
                select(MonitoringResultModel)
                .join(
                    AssetModel,
                    MonitoringResultModel.asset_id
                    == AssetModel.id,
                )
            )

            return (
                self._apply_monitoring_history_filters(
                    statement,
                    q=q,
                    status=status,
                    check_type=check_type,
                    date_from=date_from,
                    date_to=date_to,
                )
            )

        total_checks = db.scalar(
            select(
                func.count()
            ).select_from(
                filtered_statement().subquery()
            )
        ) or 0

        successful_checks = db.scalar(
            select(
                func.count()
            ).select_from(
                filtered_statement()
                .where(
                    MonitoringResultModel.status
                    == "UP"
                )
                .subquery()
            )
        ) or 0

        failed_checks = db.scalar(
            select(
                func.count()
            ).select_from(
                filtered_statement()
                .where(
                    MonitoringResultModel.status
                    == "DOWN"
                )
                .subquery()
            )
        ) or 0

        average_response_time_ms = db.scalar(
            select(
                func.avg(
                    MonitoringResultModel.response_time_ms
                )
            )
            .select_from(MonitoringResultModel)
            .join(
                AssetModel,
                MonitoringResultModel.asset_id
                == AssetModel.id,
            )
            .where(
                MonitoringResultModel.id.in_(
                    select(
                        filtered_statement()
                        .subquery()
                        .c.id
                    )
                )
            )
        )

        return {
            "total_checks": total_checks,
            "successful_checks": successful_checks,
            "failed_checks": failed_checks,
            "average_response_time_ms": (
                float(average_response_time_ms)
                if average_response_time_ms
                is not None
                else None
            ),
        }


    def get_recent_monitoring_history(
        self,
        db: Session,
        *,
        q: str | None = None,
        status: str | None = None,
        check_type: str | None = None,
        date_from=None,
        date_to=None,
        limit: int = 20,
    ) -> list[dict]:
        statement = (
            select(
                AssetModel,
                MonitoringResultModel,
            )
            .join(
                MonitoringResultModel,
                MonitoringResultModel.asset_id
                == AssetModel.id,
            )
        )

        statement = (
            self._apply_monitoring_history_filters(
                statement,
                q=q,
                status=status,
                check_type=check_type,
                date_from=date_from,
                date_to=date_to,
            )
        )

        statement = (
            statement
            .order_by(
                MonitoringResultModel.checked_at.desc(),
                MonitoringResultModel.id.desc(),
            )
            .limit(limit)
        )

        rows = db.execute(statement).all()

        return [
            {
                "asset": asset,
                "result": result,
            }
            for asset, result in rows
        ]

    def get_monitoring_filter_options(
        self,
        db: Session,
    ) -> dict[str, list[str]]:
        check_types = list(
            db.execute(
                select(
                    MonitoringConfigModel.check_type
                )
                .where(
                    MonitoringConfigModel.enabled.is_(
                        True
                    )
                )
                .distinct()
                .order_by(
                    MonitoringConfigModel.check_type.asc()
                )
            ).scalars().all()
        )

        statuses = list(
            db.execute(
                select(
                    MonitoringResultModel.status
                )
                .distinct()
                .order_by(
                    MonitoringResultModel.status.asc()
                )
            ).scalars().all()
        )

        if "UNKNOWN" not in statuses:
            statuses.append("UNKNOWN")

        return {
            "check_types": check_types,
            "statuses": statuses,
        }


    def _apply_audit_filters(
        self,
        statement,
        *,
        actor: str | None = None,
        action: str | None = None,
        resource_type: str | None = None,
        status: str | None = None,
        date_from=None,
        date_to=None,
    ):
        if actor:
            search = f"%{actor.strip()}%"

            statement = statement.where(
                AuditLogModel.actor_username.ilike(
                    search
                )
            )

        if action:
            statement = statement.where(
                AuditLogModel.action == action
            )

        if resource_type:
            statement = statement.where(
                AuditLogModel.resource_type
                == resource_type
            )

        if status:
            statement = statement.where(
                AuditLogModel.status == status
            )

        if date_from is not None:
            statement = statement.where(
                AuditLogModel.created_at
                >= date_from
            )

        if date_to is not None:
            statement = statement.where(
                AuditLogModel.created_at
                <= date_to
            )

        return statement

    def get_audit_summary(
        self,
        db: Session,
        *,
        actor: str | None = None,
        action: str | None = None,
        resource_type: str | None = None,
        status: str | None = None,
        date_from=None,
        date_to=None,
    ) -> dict:
        def filtered_statement():
            statement = select(
                AuditLogModel
            )

            return self._apply_audit_filters(
                statement,
                actor=actor,
                action=action,
                resource_type=resource_type,
                status=status,
                date_from=date_from,
                date_to=date_to,
            )

        total_events = db.scalar(
            select(
                func.count()
            ).select_from(
                filtered_statement().subquery()
            )
        ) or 0

        def count_status(
            value: str,
        ) -> int:
            statement = (
                filtered_statement()
                .where(
                    AuditLogModel.status == value
                )
            )

            return db.scalar(
                select(
                    func.count()
                ).select_from(
                    statement.subquery()
                )
            ) or 0

        return {
            "total_events": total_events,
            "success_events": count_status(
                "SUCCESS"
            ),
            "failure_events": count_status(
                "FAILURE"
            ),
            "blocked_events": count_status(
                "BLOCKED"
            ),
        }

    def get_audit_breakdown(
        self,
        db: Session,
        *,
        actor: str | None = None,
        action: str | None = None,
        resource_type: str | None = None,
        status: str | None = None,
        date_from=None,
        date_to=None,
    ) -> dict[str, int]:
        statement = select(
            AuditLogModel.resource_type,
            func.count(
                AuditLogModel.id
            ),
        )

        statement = self._apply_audit_filters(
            statement,
            actor=actor,
            action=action,
            resource_type=resource_type,
            status=status,
            date_from=date_from,
            date_to=date_to,
        )

        statement = (
            statement
            .group_by(
                AuditLogModel.resource_type
            )
        )

        rows = db.execute(
            statement
        ).all()

        categories = {
            "authentication": 0,
            "assets": 0,
            "monitoring": 0,
            "users": 0,
            "other": 0,
        }

        for resource, count in rows:
            normalized = (
                resource or ""
            ).upper()

            if normalized == "AUTHENTICATION":
                category = "authentication"
            elif normalized == "ASSET":
                category = "assets"
            elif normalized in {
                "MONITORING_CONFIG",
                "MONITORING_RESULT",
            }:
                category = "monitoring"
            elif normalized == "USER":
                category = "users"
            else:
                category = "other"

            categories[category] += count

        return categories

    def get_recent_audit_activity(
        self,
        db: Session,
        *,
        actor: str | None = None,
        action: str | None = None,
        resource_type: str | None = None,
        status: str | None = None,
        date_from=None,
        date_to=None,
        limit: int = 50,
    ) -> list[AuditLogModel]:
        statement = select(
            AuditLogModel
        )

        statement = self._apply_audit_filters(
            statement,
            actor=actor,
            action=action,
            resource_type=resource_type,
            status=status,
            date_from=date_from,
            date_to=date_to,
        )

        statement = (
            statement
            .order_by(
                AuditLogModel.created_at.desc(),
                AuditLogModel.id.desc(),
            )
            .limit(limit)
        )

        return list(
            db.execute(
                statement
            ).scalars().all()
        )

    def get_audit_filter_options(
        self,
        db: Session,
    ) -> dict[str, list[str]]:
        def distinct_values(column):
            return list(
                db.execute(
                    select(column)
                    .where(
                        column.is_not(None)
                    )
                    .distinct()
                    .order_by(
                        column.asc()
                    )
                ).scalars().all()
            )

        return {
            "actions": distinct_values(
                AuditLogModel.action
            ),
            "resource_types": distinct_values(
                AuditLogModel.resource_type
            ),
            "statuses": distinct_values(
                AuditLogModel.status
            ),
        }


report_repository = ReportRepository()
