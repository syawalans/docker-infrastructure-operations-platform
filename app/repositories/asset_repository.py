from app.schemas.asset import Asset


class AssetRepository:
    def __init__(self):
        self._assets: list[Asset] = []

    def get_all(self) -> list[Asset]:
        return self._assets

    def count(self) -> int:
        return len(self._assets)


asset_repository = AssetRepository()
