from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.asset import AssetModel


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


report_repository = ReportRepository()
