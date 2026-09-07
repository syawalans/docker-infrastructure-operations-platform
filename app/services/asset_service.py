from app.repositories.asset_repository import asset_repository


class AssetService:
    def get_dashboard_data(self):
        assets = asset_repository.get_all()

        return {
            "total_assets": len(assets),
            "servers": sum(
                1 for asset in assets
                if asset.asset_type.lower() == "server"
            ),
            "network_devices": sum(
                1 for asset in assets
                if asset.asset_type.lower()
                in {"switch", "router", "firewall", "access point"}
            ),
            "offline_assets": sum(
                1 for asset in assets
                if asset.status.lower() == "inactive"
            ),
            "assets": assets,
        }


asset_service = AssetService()
