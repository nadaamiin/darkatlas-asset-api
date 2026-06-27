from pydantic import BaseModel, Field, model_validator
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
    type: AssetType
    value: str
    status: AssetStatus = AssetStatus.active
    source: str
    tags: list[str] = []
    metadata: dict = {}


# Inherited from AssetCreate, but allows for an optional ID field for importing assets
class AssetImport(AssetCreate):
    id: Optional[str] = None

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

    @model_validator(mode='before')
    @classmethod
    def extract_metadata(cls, values):
        if hasattr(values, '__dict__'):
            data = {}
            for key in ['id', 'type', 'value', 'status', 'first_seen', 
                       'last_seen', 'source', 'tags']:
                data[key] = getattr(values, key, None)
            data['metadata'] = getattr(values, 'metadata_', {}) or {}
            return data
        return values

    class Config:
        from_attributes = True


# What we send back for a list of assets, includes total count and pagination info
class AssetListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[AssetResponse]




# Relationship schemas
class RelationshipCreate(BaseModel):
    source_id: str      # eg. Domain 
    target_id: str      # eg. Subdomain
    relationship_type: str  # eg. belongs to


class RelationshipResponse(BaseModel):
    id: str
    source_id: str
    target_id: str
    relationship_type: str
    created_at: datetime

    class Config:
        from_attributes = True


# Combines one asset with its related relationships and related assets
class AssetGraphResponse(BaseModel):
    asset: AssetResponse
    relationships: list[RelationshipResponse]
    related_assets: list[AssetResponse]