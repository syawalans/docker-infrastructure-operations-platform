from pydantic import BaseModel


class Asset(BaseModel):
    id: int
    name: str
    hostname: str
    asset_type: str
    vendor: str | None = None
    model: str | None = None
    ip_address: str
    operating_system: str | None = None
    environment: str
    location: str | None = None
    status: str
    description: str | None = None
