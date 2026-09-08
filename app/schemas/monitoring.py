from pydantic import BaseModel, Field


class MonitoringConfigCreate(BaseModel):
    asset_id: int
    check_type: str
    target: str
    port: int | None = Field(
        default=None,
        ge=1,
        le=65535,
    )
    http_path: str | None = None
    interval_seconds: int = Field(
        default=60,
        ge=10,
    )
    timeout_seconds: int = Field(
        default=5,
        ge=1,
        le=60,
    )
    enabled: bool = True
