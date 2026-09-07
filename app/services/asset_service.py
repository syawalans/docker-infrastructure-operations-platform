from sqlalchemy.orm import Session

from app.repositories.asset_repository import asset_repository
from app.schemas.asset import AssetCreate


class AssetService:
    def get_all_assets(self, db: Session):
        return asset_repository.get_all(db)

    def get_asset(
        self,
        db: Session,
        asset_id: int,
    ):
        return asset_repository.get_by_id(
            db,
            asset_id,
        )

    def create_asset(
        self,
        db: Session,
        asset_data: AssetCreate,
    ):
        return asset_repository.create(
            db,
            asset_data,
        )

    def get_dashboard_data(
        self,
        db: Session,
    ):
        assets = asset_repository.get_all(db)

        return {
            "total_assets": len(assets),
            "servers": sum(
                1
                for asset in assets
                if asset.asset_type.lower() == "server"
            ),
            "network_devices": sum(
                1
                for asset in assets
                if asset.asset_type.lower()
                in {
                    "switch",
                    "router",
                    "firewall",
                    "access point",
                }
            ),
            "offline_assets": sum(
                1
                for asset in assets
                if asset.status.lower() == "inactive"
            ),
            "assets": assets,
        }


asset_service = AssetService()