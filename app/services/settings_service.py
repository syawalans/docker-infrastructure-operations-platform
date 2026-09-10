from typing import Any

from sqlalchemy.orm import Session

from app.core.settings_registry import (
    DEFAULT_SYSTEM_SETTINGS,
)
from app.models.setting import SystemSettingModel
from app.repositories.settings_repository import (
    settings_repository,
)


SUPPORTED_VALUE_TYPES = {
    "string",
    "integer",
    "boolean",
}


class SettingsService:
    def initialize_defaults(
        self,
        db: Session,
    ) -> dict[str, int]:
        created = 0
        existing = 0

        for definition in DEFAULT_SYSTEM_SETTINGS:
            current = settings_repository.get_by_key(
                db,
                definition["category"],
                definition["setting_key"],
            )

            if current is not None:
                existing += 1
                continue

            settings_repository.create(
                db,
                category=definition["category"],
                setting_key=definition["setting_key"],
                setting_value=definition["setting_value"],
                value_type=definition["value_type"],
                description=definition["description"],
                is_editable=definition["is_editable"],
            )

            created += 1

        return {
            "created": created,
            "existing": existing,
        }

    def get_all(
        self,
        db: Session,
    ) -> list[SystemSettingModel]:
        return settings_repository.get_all(db)

    def get_by_category(
        self,
        db: Session,
        category: str,
    ) -> list[SystemSettingModel]:
        return settings_repository.get_by_category(
            db,
            category,
        )

    def get_setting(
        self,
        db: Session,
        category: str,
        setting_key: str,
    ) -> SystemSettingModel | None:
        return settings_repository.get_by_key(
            db,
            category,
            setting_key,
        )

    def get_value(
        self,
        db: Session,
        category: str,
        setting_key: str,
        default: Any = None,
    ) -> Any:
        setting = self.get_setting(
            db,
            category,
            setting_key,
        )

        if setting is None:
            return default

        return self.deserialize_value(
            setting
        )

    def get_category_values(
        self,
        db: Session,
        category: str,
    ) -> dict[str, Any]:
        settings = self.get_by_category(
            db,
            category,
        )

        return {
            setting.setting_key: (
                self.deserialize_value(setting)
            )
            for setting in settings
        }

    def deserialize_value(
        self,
        setting: SystemSettingModel,
    ) -> Any:
        if setting.value_type == "integer":
            return int(setting.setting_value)

        if setting.value_type == "boolean":
            return (
                setting.setting_value.strip().lower()
                == "true"
            )

        return setting.setting_value

    def serialize_value(
        self,
        value: Any,
        value_type: str,
    ) -> str:
        if value_type not in SUPPORTED_VALUE_TYPES:
            raise ValueError(
                "Unsupported setting value type."
            )

        if value_type == "integer":
            if isinstance(value, bool):
                raise ValueError(
                    "Boolean value cannot be stored as integer."
                )

            try:
                return str(int(value))
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    "Setting value must be an integer."
                ) from exc

        if value_type == "boolean":
            if isinstance(value, bool):
                return "true" if value else "false"

            normalized = str(value).strip().lower()

            if normalized not in {
                "true",
                "false",
            }:
                raise ValueError(
                    "Setting value must be true or false."
                )

            return normalized

        return str(value).strip()

    def create_setting(
        self,
        db: Session,
        *,
        category: str,
        setting_key: str,
        setting_value: Any,
        value_type: str = "string",
        description: str | None = None,
        is_editable: bool = True,
        updated_by: int | None = None,
    ) -> SystemSettingModel:
        category = category.strip().lower()
        setting_key = setting_key.strip().lower()

        if not category:
            raise ValueError(
                "Setting category is required."
            )

        if not setting_key:
            raise ValueError(
                "Setting key is required."
            )

        existing = settings_repository.get_by_key(
            db,
            category,
            setting_key,
        )

        if existing is not None:
            raise ValueError(
                "Setting already exists."
            )

        serialized_value = self.serialize_value(
            setting_value,
            value_type,
        )

        return settings_repository.create(
            db,
            category=category,
            setting_key=setting_key,
            setting_value=serialized_value,
            value_type=value_type,
            description=description,
            is_editable=is_editable,
            updated_by=updated_by,
        )

    def update_setting(
        self,
        db: Session,
        *,
        category: str,
        setting_key: str,
        setting_value: Any,
        updated_by: int | None = None,
    ) -> SystemSettingModel:
        setting = settings_repository.get_by_key(
            db,
            category.strip().lower(),
            setting_key.strip().lower(),
        )

        if setting is None:
            raise ValueError(
                "Setting not found."
            )

        if not setting.is_editable:
            raise ValueError(
                "This setting is read-only."
            )

        serialized_value = self.serialize_value(
            setting_value,
            setting.value_type,
        )

        return settings_repository.update(
            db,
            setting,
            setting_value=serialized_value,
            updated_by=updated_by,
        )


settings_service = SettingsService()
