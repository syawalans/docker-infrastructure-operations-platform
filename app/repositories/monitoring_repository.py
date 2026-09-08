from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.asset import AssetModel
from app.models.monitoring import (
    MonitoringConfigModel,
    MonitoringResultModel,
)
from app.schemas.monitoring import MonitoringConfigCreate


class MonitoringRepository:
    def get_config_by_asset(
        self,
        db: Session,
        asset_id: int,
    ) -> MonitoringConfigModel | None:
        statement = (
            select(MonitoringConfigModel)
            .where(
                MonitoringConfigModel.asset_id == asset_id
            )
            .order_by(MonitoringConfigModel.id.desc())
            .limit(1)
        )

        return db.execute(
            statement
        ).scalar_one_or_none()

    def create_config(
        self,
        db: Session,
        data: MonitoringConfigCreate,
    ) -> MonitoringConfigModel:
        config = MonitoringConfigModel(
            asset_id=data.asset_id,
            check_type=data.check_type,
            target=data.target,
            port=data.port,
            http_path=data.http_path,
            interval_seconds=data.interval_seconds,
            timeout_seconds=data.timeout_seconds,
            enabled=data.enabled,
        )

        db.add(config)
        db.commit()
        db.refresh(config)

        return config

    def update_config(
        self,
        db: Session,
        config: MonitoringConfigModel,
        data: MonitoringConfigCreate,
    ) -> MonitoringConfigModel:
        config.check_type = data.check_type
        config.target = data.target
        config.port = data.port
        config.http_path = data.http_path
        config.interval_seconds = data.interval_seconds
        config.timeout_seconds = data.timeout_seconds
        config.enabled = data.enabled

        db.commit()
        db.refresh(config)

        return config

    def delete_config(
        self,
        db: Session,
        config: MonitoringConfigModel,
    ) -> None:
        db.delete(config)
        db.commit()

    def create_result(
        self,
        db: Session,
        *,
        asset_id: int,
        config_id: int,
        check_type: str,
        target: str,
        port: int | None,
        http_path: str | None,
        status: str,
        response_time_ms: float | None,
        error_message: str | None,
    ) -> MonitoringResultModel:
        result = MonitoringResultModel(
            asset_id=asset_id,
            config_id=config_id,
            check_type=check_type,
            target=target,
            port=port,
            http_path=http_path,
            status=status,
            response_time_ms=response_time_ms,
            error_message=error_message,
        )

        db.add(result)
        db.commit()
        db.refresh(result)

        return result

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
