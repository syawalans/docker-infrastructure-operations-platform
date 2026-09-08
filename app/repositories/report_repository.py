from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.asset import AssetModel
from app.models.monitoring import (
    MonitoringConfigModel,
    MonitoringResultModel,
)


class ReportRepository:
    def get_asset_inventory(
        self,
        db: Session,
    ) -> list[AssetModel]:
        statement = (
            select(AssetModel)
            .order_by(
                AssetModel.hostname.asc()
            )
        )

        result = db.execute(statement)

        return list(
            result.scalars().all()
        )

    def get_asset_summary(
        self,
        db: Session,
    ) -> dict[str, int]:
        total_assets = db.scalar(
            select(
                func.count(AssetModel.id)
            )
        ) or 0

        active_assets = db.scalar(
            select(
                func.count(AssetModel.id)
            ).where(
                AssetModel.status == "Active"
            )
        ) or 0

        maintenance_assets = db.scalar(
            select(
                func.count(AssetModel.id)
            ).where(
                AssetModel.status == "Maintenance"
            )
        ) or 0

        inactive_assets = db.scalar(
            select(
                func.count(AssetModel.id)
            ).where(
                AssetModel.status == "Inactive"
            )
        ) or 0

        return {
            "total_assets": total_assets,
            "active_assets": active_assets,
            "maintenance_assets": maintenance_assets,
            "inactive_assets": inactive_assets,
        }


    def get_monitoring_report(
        self,
        db: Session,
    ) -> list[dict]:
        configs = list(
            db.execute(
                select(MonitoringConfigModel)
                .where(
                    MonitoringConfigModel.enabled.is_(True)
                )
                .order_by(
                    MonitoringConfigModel.asset_id.asc()
                )
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

            rows.append(
                {
                    "asset": asset,
                    "config": config,
                    "latest_result": latest_result,
                }
            )

        return rows


    def get_monitoring_history_summary(
        self,
        db: Session,
    ) -> dict:
        total_checks = db.scalar(
            select(
                func.count(
                    MonitoringResultModel.id
                )
            )
        ) or 0

        successful_checks = db.scalar(
            select(
                func.count(
                    MonitoringResultModel.id
                )
            ).where(
                MonitoringResultModel.status == "UP"
            )
        ) or 0

        failed_checks = db.scalar(
            select(
                func.count(
                    MonitoringResultModel.id
                )
            ).where(
                MonitoringResultModel.status == "DOWN"
            )
        ) or 0

        average_response_time_ms = db.scalar(
            select(
                func.avg(
                    MonitoringResultModel.response_time_ms
                )
            )
        )

        return {
            "total_checks": total_checks,
            "successful_checks": successful_checks,
            "failed_checks": failed_checks,
            "average_response_time_ms": (
                float(average_response_time_ms)
                if average_response_time_ms is not None
                else None
            ),
        }

    def get_recent_monitoring_history(
        self,
        db: Session,
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


report_repository = ReportRepository()
