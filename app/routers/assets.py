from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.asset import (
    AssetCreate, AssetImport, AssetUpdate,
    AssetResponse, AssetListResponse,
    RelationshipCreate, RelationshipResponse, AssetGraphResponse
)
from app.services.asset_service import (
    get_asset, get_assets, create_asset,
    update_asset, delete_asset, mark_stale,
    create_relationship, get_asset_relationships, get_asset_graph
)
from app.models.relationship import AssetRelationship


router = APIRouter(prefix="/assets", tags=["Assets"])


@router.get("/", response_model=AssetListResponse)
def list_assets(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    type: str = Query(None),
    status: str = Query(None),
    tag: str = Query(None),
    value_contains: str = Query(None),
    sort_by: str = Query("last_seen"),
    sort_order: str = Query("desc"),
    db: Session = Depends(get_db)
):
    total, items = get_assets(
        db, page, page_size, type,
        status, tag, value_contains,
        sort_by, sort_order
    )
    return AssetListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=items
    )


@router.get("/{asset_id}", response_model=AssetResponse)
def read_asset(asset_id: str, db: Session = Depends(get_db)):
    asset = get_asset(db, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


@router.post("/", response_model=AssetResponse, status_code=201)
def create_asset_endpoint(
    asset_in: AssetCreate,
    db: Session = Depends(get_db)
):
    return create_asset(db, asset_in)


@router.patch("/{asset_id}", response_model=AssetResponse)
def update_asset_endpoint(
    asset_id: str,
    asset_in: AssetUpdate,
    db: Session = Depends(get_db)
):
    asset = update_asset(db, asset_id, asset_in)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


@router.delete("/{asset_id}", status_code=204)
def delete_asset_endpoint(
    asset_id: str,
    db: Session = Depends(get_db)
):
    success = delete_asset(db, asset_id)
    if not success:
        raise HTTPException(status_code=404, detail="Asset not found")


@router.post("/bulk", response_model=dict)
def bulk_import(
    assets: list[AssetImport],
    db: Session = Depends(get_db)
):
    created = 0
    updated = 0
    failed = 0
    errors = []

    for i, asset_in in enumerate(assets):
        try:
            existing = get_asset(db, asset_in.id) if asset_in.id else None
            result = create_asset(db, asset_in)
            if existing:
                updated += 1
            else:
                created += 1
        except Exception as e:
            failed += 1
            errors.append({"index": i, "error": str(e)})

    return {
        "created": created,
        "updated": updated,
        "failed": failed,
        "errors": errors
    }


@router.post("/mark-stale", response_model=dict)
def mark_stale_endpoint(
    days: int = Query(30, ge=1),
    db: Session = Depends(get_db)
):
    count = mark_stale(db, days)
    return {"marked_stale": count}
@router.post("/relationships", response_model=RelationshipResponse)
def create_relationship_endpoint(
    rel_in: RelationshipCreate,
    db: Session = Depends(get_db)
):
    relationship = create_relationship(
        db,
        rel_in.source_id,
        rel_in.target_id,
        rel_in.relationship_type
    )
    if not relationship:
        raise HTTPException(
            status_code=404,
            detail="One or both assets not found"
        )
    return relationship


@router.get("/{asset_id}/relationships", response_model=list[RelationshipResponse])
def get_relationships_endpoint(
    asset_id: str,
    db: Session = Depends(get_db)
):
    asset = get_asset(db, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return get_asset_relationships(db, asset_id)


@router.get("/{asset_id}/graph", response_model=AssetGraphResponse)
def get_asset_graph_endpoint(
    asset_id: str,
    db: Session = Depends(get_db)
):
    graph = get_asset_graph(db, asset_id)
    if not graph:
        raise HTTPException(status_code=404, detail="Asset not found")
    return graph