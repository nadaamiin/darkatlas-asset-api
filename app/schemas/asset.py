from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class AssetType(str, Enum):
    domain = "domain"
    subdomain = "subdomain"
    ip_address = "ip_address"
    service = "service"
    certificate = "certificate"
    technology = "technology"


class AssetStatus(str, Enum):
    active = "active"
    stale = "stale"
    archived = "archived"


# What the user sends when creating an asset
class AssetCreate(BaseModel):
    id: Optional[str] = None        # Optional, generate it if not provided
    type: AssetType
    value: str
    status: AssetStatus = AssetStatus.active
    source: str
    tags: list[str] = []
    metadata: dict = {}


# What the user sends when updating an asset and what fields can be updated
class AssetUpdate(BaseModel):
    status: Optional[AssetStatus] = None
    tags: Optional[list[str]] = None
    metadata: Optional[dict] = None
    source: Optional[str] = None


# What we send back to the user
class AssetResponse(BaseModel):
    id: str
    type: AssetType
    value: str
    status: AssetStatus
    first_seen: datetime
    last_seen: datetime
    source: str
    tags: list[str]
    metadata: dict

    class Config:
        from_attributes = True


# What we send back for a list of assets, includes total count and pagination info
class AssetListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[AssetResponse]