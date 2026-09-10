from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.setting import SystemSettingModel


class SettingsRepository:
    def get_all(
        self,
        db: Session,
    ) -> list[SystemSettingModel]:
        statement = (
            select(SystemSettingModel)
            .order_by(
                SystemSettingModel.category.asc(),
                SystemSettingModel.setting_key.asc(),
            )
        )

        return list(
            db.execute(statement).scalars().all()
        )

    def get_by_category(
        self,
        db: Session,
        category: str,
    ) -> list[SystemSettingModel]:
        statement = (
            select(SystemSettingModel)
            .where(
                SystemSettingModel.category == category
            )
            .order_by(
                SystemSettingModel.setting_key.asc()
            )
        )

        return list(
            db.execute(statement).scalars().all()
        )

    def get_by_key(
        self,
        db: Session,
        category: str,
        setting_key: str,
    ) -> SystemSettingModel | None:
        statement = (
            select(SystemSettingModel)
            .where(
                SystemSettingModel.category == category,
                SystemSettingModel.setting_key == setting_key,
            )
            .limit(1)
        )

        return db.execute(
            statement
        ).scalar_one_or_none()

    def create(
        self,
        db: Session,
        *,
        category: str,
        setting_key: str,
        setting_value: str,
        value_type: str,
        description: str | None,
        is_editable: bool,
        updated_by: int | None = None,
    ) -> SystemSettingModel:
        setting = SystemSettingModel(
            category=category,
            setting_key=setting_key,
            setting_value=setting_value,
            value_type=value_type,
            description=description,
            is_editable=is_editable,
            updated_by=updated_by,
        )

        db.add(setting)
        db.commit()
        db.refresh(setting)

        return setting

    def update(
        self,
        db: Session,
        setting: SystemSettingModel,
        *,
        setting_value: str,
        updated_by: int | None = None,
    ) -> SystemSettingModel:
        setting.setting_value = setting_value
        setting.updated_by = updated_by

        db.commit()
        db.refresh(setting)

        return setting


settings_repository = SettingsRepository()
