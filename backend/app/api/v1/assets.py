"""Assets management endpoints."""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.permissions import Permission
from app.infrastructure.database import get_db
from app.infrastructure.database.models import Asset, AssetType, AssetStatus, Severity, User
from app.api.v1.deps import get_current_active_user, require_permission

router = APIRouter()


# Schemas
class AssetBase(BaseModel):
    name: str
    asset_type: AssetType
    status: AssetStatus = AssetStatus.ACTIVE
    criticality: Severity = Severity.MEDIUM
    ip_address: str | None = None
    mac_address: str | None = None
    hostname: str | None = None
    fqdn: str | None = None
    os: str | None = None
    os_version: str | None = None
    location: str | None = None
    department: str | None = None
    owner: str | None = None
    tags: List[str] = []
    notes: str | None = None


class AssetCreate(AssetBase):
    pass


class AssetUpdate(BaseModel):
    name: str | None = None
    asset_type: AssetType | None = None
    status: AssetStatus | None = None
    criticality: Severity | None = None
    ip_address: str | None = None
    mac_address: str | None = None
    hostname: str | None = None
    fqdn: str | None = None
    os: str | None = None
    os_version: str | None = None
    location: str | None = None
    department: str | None = None
    owner: str | None = None
    tags: List[str] | None = None
    notes: str | None = None


class AssetResponse(AssetBase):
    id: str
    services: List[dict] = []
    custom_fields: dict = {}
    vulnerability_count: int = 0
    created_at: str
    updated_at: str | None

    class Config:
        from_attributes = True


class AssetListResponse(BaseModel):
    items: List[AssetResponse]
    total: int
    skip: int
    limit: int


# Endpoints
@router.get("/", response_model=AssetListResponse)
async def list_assets(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    asset_type: Optional[AssetType] = None,
    status: Optional[AssetStatus] = None,
    criticality: Optional[Severity] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.ASSET_VIEW)),
):
    """List assets with optional filters."""
    query = db.query(Asset)

    # Apply filters
    if asset_type:
        query = query.filter(Asset.asset_type == asset_type)
    if status:
        query = query.filter(Asset.status == status)
    if criticality:
        query = query.filter(Asset.criticality == criticality)
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (Asset.name.ilike(search_filter))
            | (Asset.hostname.ilike(search_filter))
            | (Asset.ip_address.ilike(search_filter))
        )

    total = query.count()
    assets = query.order_by(Asset.created_at.desc()).offset(skip).limit(limit).all()

    return AssetListResponse(
        items=[
            AssetResponse(
                id=str(a.id),
                name=a.name,
                asset_type=a.asset_type,
                status=a.status,
                criticality=a.criticality,
                ip_address=a.ip_address,
                mac_address=a.mac_address,
                hostname=a.hostname,
                fqdn=a.fqdn,
                os=a.os,
                os_version=a.os_version,
                location=a.location,
                department=a.department,
                owner=a.owner,
                tags=a.tags or [],
                notes=a.notes,
                services=a.services or [],
                custom_fields=a.custom_fields or {},
                vulnerability_count=len(a.vulnerabilities),
                created_at=a.created_at.isoformat(),
                updated_at=a.updated_at.isoformat() if a.updated_at else None,
            )
            for a in assets
        ],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset(
    asset_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.ASSET_VIEW)),
):
    """Get a specific asset."""
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found",
        )

    return AssetResponse(
        id=str(asset.id),
        name=asset.name,
        asset_type=asset.asset_type,
        status=asset.status,
        criticality=asset.criticality,
        ip_address=asset.ip_address,
        mac_address=asset.mac_address,
        hostname=asset.hostname,
        fqdn=asset.fqdn,
        os=asset.os,
        os_version=asset.os_version,
        location=asset.location,
        department=asset.department,
        owner=asset.owner,
        tags=asset.tags or [],
        notes=asset.notes,
        services=asset.services or [],
        custom_fields=asset.custom_fields or {},
        vulnerability_count=len(asset.vulnerabilities),
        created_at=asset.created_at.isoformat(),
        updated_at=asset.updated_at.isoformat() if asset.updated_at else None,
    )


@router.post("/", response_model=AssetResponse, status_code=status.HTTP_201_CREATED)
async def create_asset(
    asset_data: AssetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.ASSET_CREATE)),
):
    """Create a new asset."""
    asset = Asset(
        name=asset_data.name,
        asset_type=asset_data.asset_type,
        status=asset_data.status,
        criticality=asset_data.criticality,
        ip_address=asset_data.ip_address,
        mac_address=asset_data.mac_address,
        hostname=asset_data.hostname,
        fqdn=asset_data.fqdn,
        os=asset_data.os,
        os_version=asset_data.os_version,
        location=asset_data.location,
        department=asset_data.department,
        owner=asset_data.owner,
        tags=asset_data.tags,
        notes=asset_data.notes,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)

    return AssetResponse(
        id=str(asset.id),
        name=asset.name,
        asset_type=asset.asset_type,
        status=asset.status,
        criticality=asset.criticality,
        ip_address=asset.ip_address,
        mac_address=asset.mac_address,
        hostname=asset.hostname,
        fqdn=asset.fqdn,
        os=asset.os,
        os_version=asset.os_version,
        location=asset.location,
        department=asset.department,
        owner=asset.owner,
        tags=asset.tags or [],
        notes=asset.notes,
        services=asset.services or [],
        custom_fields=asset.custom_fields or {},
        vulnerability_count=0,
        created_at=asset.created_at.isoformat(),
        updated_at=None,
    )


@router.patch("/{asset_id}", response_model=AssetResponse)
async def update_asset(
    asset_id: UUID,
    asset_data: AssetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.ASSET_EDIT)),
):
    """Update an asset."""
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found",
        )

    update_data = asset_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(asset, field, value)

    db.commit()
    db.refresh(asset)

    return AssetResponse(
        id=str(asset.id),
        name=asset.name,
        asset_type=asset.asset_type,
        status=asset.status,
        criticality=asset.criticality,
        ip_address=asset.ip_address,
        mac_address=asset.mac_address,
        hostname=asset.hostname,
        fqdn=asset.fqdn,
        os=asset.os,
        os_version=asset.os_version,
        location=asset.location,
        department=asset.department,
        owner=asset.owner,
        tags=asset.tags or [],
        notes=asset.notes,
        services=asset.services or [],
        custom_fields=asset.custom_fields or {},
        vulnerability_count=len(asset.vulnerabilities),
        created_at=asset.created_at.isoformat(),
        updated_at=asset.updated_at.isoformat() if asset.updated_at else None,
    )


@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_asset(
    asset_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.ASSET_DELETE)),
):
    """Delete an asset."""
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found",
        )

    db.delete(asset)
    db.commit()


# Statistics
@router.get("/stats/summary")
async def get_assets_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.ASSET_VIEW)),
):
    """Get assets statistics."""
    total = db.query(Asset).count()

    # By type
    by_type = {}
    for asset_type in AssetType:
        count = db.query(Asset).filter(Asset.asset_type == asset_type).count()
        if count > 0:
            by_type[asset_type.value] = count

    # By status
    by_status = {}
    for status in AssetStatus:
        count = db.query(Asset).filter(Asset.status == status).count()
        if count > 0:
            by_status[status.value] = count

    # By criticality
    by_criticality = {}
    for criticality in Severity:
        count = db.query(Asset).filter(Asset.criticality == criticality).count()
        if count > 0:
            by_criticality[criticality.value] = count

    return {
        "total": total,
        "by_type": by_type,
        "by_status": by_status,
        "by_criticality": by_criticality,
    }
