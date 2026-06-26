import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.asset import Asset, AssetStatus
from app.schemas.asset import AssetCreate, AssetUpdate


# Helper to fetch one asset row from the database by ID
def get_asset(db: Session, asset_id: str):
    # Filter by ID and return the first match (or None if not found)
    return db.query(Asset).filter(Asset.id == asset_id).first()


# Fetch multiple assets with optional filtering, sorting, and pagination
def get_assets(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    type: str = None,
    status: str = None,
    tag: str = None,
    value_contains: str = None,
    sort_by: str = "last_seen",
    sort_order: str = "desc"
):
    query = db.query(Asset)

    # Filtering
    if type:
        query = query.filter(Asset.type == type)
    if status:
        query = query.filter(Asset.status == status)
    if tag:
        query = query.filter(Asset.tags.contains([tag]))
    if value_contains:
        query = query.filter(Asset.value.ilike(f"%{value_contains}%"))

    # Sorting
    # sort by can be any column of Asset; default is last_seen
    sort_column = getattr(Asset, sort_by, Asset.last_seen)
    if sort_order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    # Pagination
    # Get total count of matching rows after filtering
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    return total, items


def create_asset(db: Session, asset_in: AssetCreate):
    # Check if asset already exists by value + type to avoid duplicates 
    existing = db.query(Asset).filter(
        Asset.value == asset_in.value,
        Asset.type == asset_in.type).first()

    if existing:
        # If asset exists, update its last_seen timestamp and the source
        existing.last_seen = datetime.now(timezone.utc)
        existing.source = asset_in.source

        # Merge tags, combining existing and new tags without duplicates
        existing_tags = existing.tags or []
        new_tags = [t for t in asset_in.tags if t not in existing_tags]
        existing.tags = existing_tags + new_tags

        # Merge metadata, new values override old ones
        existing_metadata = existing.metadata_ or {}
        existing_metadata.update(asset_in.metadata)
        existing.metadata_ = existing_metadata

        # If asset was stale, reactivate it
        if existing.status == AssetStatus.stale:
            existing.status = AssetStatus.active

        db.commit()
        db.refresh(existing)
        return existing

    # If a new asset, create it with a new record
    asset = Asset(
        id=asset_in.id or str(uuid.uuid4()),
        type=asset_in.type,
        value=asset_in.value,
        status=asset_in.status,
        source=asset_in.source,
        tags=asset_in.tags,
        metadata_=asset_in.metadata,
        first_seen=datetime.now(timezone.utc),
        last_seen=datetime.now(timezone.utc)
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


def update_asset(db: Session, asset_id: str, asset_in: AssetUpdate):
    asset = get_asset(db, asset_id)
    if not asset:
        return None

    # Only update fields that were sent in the request
    if asset_in.status is not None:
        asset.status = asset_in.status
    if asset_in.tags is not None:
        asset.tags = asset_in.tags
    if asset_in.metadata is not None:
        asset.metadata_ = asset_in.metadata
    if asset_in.source is not None:
        asset.source = asset_in.source

    asset.last_seen = datetime.now(timezone.utc)
    db.commit()
    db.refresh(asset)
    return asset


def delete_asset(db: Session, asset_id: str):
    asset = get_asset(db, asset_id)
    if not asset:
        return False
    db.delete(asset)
    db.commit()
    return True


def mark_stale(db: Session, days: int = 30):
    # Mark assets as stale if not seen in specific days
    from datetime import timedelta
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    assets = db.query(Asset).filter(
        Asset.last_seen < cutoff,
        Asset.status == AssetStatus.active).all()

    for asset in assets:
        asset.status = AssetStatus.stale

    db.commit()
    return len(assets)