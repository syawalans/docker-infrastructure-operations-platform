from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.asset import AssetModel
from app.schemas.asset import Asset, AssetCreate


class AssetRepository:
    def get_all(
        self,
        db: Session,
    ) -> list[Asset]:
        return self.search(db)

    def search(
        self,
        db: Session,
        query: str | None = None,
        asset_type: str | None = None,
        environment: str | None = None,
        status: str | None = None,
    ) -> list[Asset]:
        statement = select(AssetModel)

        if query:
            search_term = f"%{query.strip()}%"

            statement = statement.where(
                or_(
                    AssetModel.name.ilike(search_term),
                    AssetModel.hostname.ilike(search_term),
                    AssetModel.ip_address.ilike(search_term),
                    AssetModel.vendor.ilike(search_term),
                    AssetModel.model.ilike(search_term),
                    AssetModel.location.ilike(search_term),
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

        statement = statement.order_by(
            AssetModel.id.desc()
        )

        result = db.execute(statement)
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
