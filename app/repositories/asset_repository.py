from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.asset import AssetModel
from app.schemas.asset import Asset, AssetCreate


class AssetRepository:
    def get_all(
        self,
        db: Session,
    ) -> list[Asset]:
        result = db.execute(
            select(AssetModel).order_by(AssetModel.id.desc())
        )
        rows = result.scalars().all()

        return [
            self._to_schema(row)
            for row in rows
        ]

    def get_by_id(
        self,
        db: Session,
        asset_id: int,
    ) -> Asset | None:
        row = db.get(AssetModel, asset_id)

        if row is None:
            return None

        return self._to_schema(row)

    def create(
        self,
        db: Session,
        asset_data: AssetCreate,
    ) -> Asset:
        row = AssetModel(
            **asset_data.model_dump()
        )

        db.add(row)
        db.commit()
        db.refresh(row)

        return self._to_schema(row)

    def update(
        self,
        db: Session,
        asset_id: int,
        asset_data: AssetCreate,
    ) -> Asset | None:
        row = db.get(AssetModel, asset_id)

        if row is None:
            return None

        for field, value in asset_data.model_dump().items():
            setattr(row, field, value)

        db.commit()
        db.refresh(row)

        return self._to_schema(row)

    def delete(
        self,
        db: Session,
        asset_id: int,
    ) -> bool:
        row = db.get(AssetModel, asset_id)

        if row is None:
            return False

        db.delete(row)
        db.commit()

        return True

    @staticmethod
    def _to_schema(
        row: AssetModel,
    ) -> Asset:
        return Asset(
            id=row.id,
            name=row.name,
            hostname=row.hostname,
            asset_type=row.asset_type,
            vendor=row.vendor,
            model=row.model,
            ip_address=row.ip_address,
            operating_system=row.operating_system,
            environment=row.environment,
            location=row.location,
            status=row.status,
            description=row.description,
        )


asset_repository = AssetRepository()
