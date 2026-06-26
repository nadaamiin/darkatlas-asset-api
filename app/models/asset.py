import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, JSON, Enum, ARRAY
import enum
from app.database import Base


# The different types of assets that are allowed to be stored in the database.
class AssetType(str, enum.Enum):
    domain = "domain"
    subdomain = "subdomain"
    ip_address = "ip_address"
    service = "service"
    certificate = "certificate"
    technology = "technology"


# The different statuses that an asset can have in the database.
class AssetStatus(str, enum.Enum):
    active = "active"
    stale = "stale"
    archived = "archived"


class Asset(Base):
    __tablename__ = "assets"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    type = Column(Enum(AssetType), nullable=False)
    value = Column(String, nullable=False)
    status = Column(Enum(AssetStatus), nullable=False, default=AssetStatus.active)
    first_seen = Column(DateTime, default=lambda: datetime.now(timezone.utc))   # Automatically set to now when the asset is first created
    last_seen = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))    # Automatically updated every time the asset record changes
    source = Column(String, nullable=False)
    tags = Column(ARRAY(String), default=[])
    metadata_ = Column("metadata", JSON, default={})    # Store additional metadata about the asset in a JSON column

