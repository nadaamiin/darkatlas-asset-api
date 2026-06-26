from sqlalchemy import Column, String, DateTime, ForeignKey
from datetime import datetime, timezone
from app.database import Base


# The table that stores the links between assets, representing relationships between them.
class AssetRelationship(Base):
    __tablename__ = "asset_relationships"

    id = Column(String, primary_key=True)
    source_id = Column(String, ForeignKey("assets.id", ondelete="CASCADE"), nullable=False)
    target_id = Column(String, ForeignKey("assets.id", ondelete="CASCADE"), nullable=False)
    relationship_type = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))