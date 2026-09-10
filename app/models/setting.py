from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class SystemSettingModel(Base):
    __tablename__ = "system_settings"

    __table_args__ = (
        UniqueConstraint(
            "category",
            "setting_key",
            name="uq_system_settings_category_key",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    setting_key: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    setting_value: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    value_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="string",
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    is_editable: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    updated_by: Mapped[int | None] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
