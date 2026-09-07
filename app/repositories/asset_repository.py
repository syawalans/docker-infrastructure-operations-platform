from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.asset import AssetModel
from app.schemas.asset import Asset, AssetCreate


class AssetRepository:
    def get_all(self, db: Session) -> list[Asset]:
        result = db.execute(
            select(AssetModel).order_by(AssetModel.id.desc())
        )

        rows = result.scalars().all()

        return [
            Asset(
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