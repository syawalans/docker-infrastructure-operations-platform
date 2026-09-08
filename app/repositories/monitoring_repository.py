from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.asset import AssetModel
from app.models.monitoring import (
    MonitoringConfigModel,
    MonitoringResultModel,
)


class MonitoringRepository:
    def get_overview(
        self,
        db: Session,
    ) -> list[dict]:
        statement = (
            select(
                AssetModel,
                MonitoringConfigModel,
            )
            .outerjoin(
                MonitoringConfigModel,
                (MonitoringConfigModel.asset_id == AssetModel.id)
                & (MonitoringConfigModel.enabled.is_(True)),
            )
            .order_by(AssetModel.id.desc())
        )

        rows = db.execute(statement).all()

        overview = []

        for asset, config in rows:
            latest_result = None

            if config is not None:
                result_statement = (
                    select(MonitoringResultModel)
                    .where(
                        MonitoringResultModel.config_id == config.id
                    )
                    .order_by(
                        MonitoringResultModel.checked_at.desc(),
                        MonitoringResultModel.id.desc(),
                    )
                    .limit(1)
                )

                latest_result = db.execute(
                    result_statement
                ).scalar_one_or_none()

            overview.append(
                {
                    "asset": asset,
                    "config": config,
                    "latest_result": latest_result,
                }
            )

        return overview


monitoring_repository = MonitoringRepository()
