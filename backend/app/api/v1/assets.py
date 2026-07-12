"""Endpoints de gestion de l'inventaire d'actifs Petrix.

Expose les opérations CRUD sur les actifs (Asset) ainsi que l'endpoint d'auto-enregistrement
utilisé par l'agent Petrix à l'installation, et un résumé statistique de l'inventaire.
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.permissions import Permission
from app.infrastructure.database import get_db
from app.infrastructure.database.models import Asset, AssetType, AssetStatus, Severity, User
from app.api.v1.deps import require_permission, get_current_active_user

router = APIRouter()


# Schémas Pydantic — requêtes et réponses de l'API d'inventaire

class AssetBase(BaseModel):
    """Champs communs à la création et à la réponse d'un actif."""

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
    """Corps de la requête POST /assets : création d'un nouvel actif."""


class AssetUpdate(BaseModel):
    """Corps de la requête PATCH /assets/{id} : mise à jour partielle d'un actif.

    Tous les champs sont optionnels ; seuls ceux fournis sont modifiés (model_dump exclude_unset).
    """

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
    """Représentation complète d'un actif retournée par l'API.

    Attributs supplémentaires par rapport à AssetBase :
        vulnerability_count: Nombre de vulnérabilités actives associées à cet actif.
        services: Liste des services ouverts (port, nom, version) issus de l'agent.
        custom_fields: Métadonnées arbitraires clé-valeur.
    """

    id: str
    services: List[dict] = []
    custom_fields: dict = {}
    vulnerability_count: int = 0
    created_at: str
    updated_at: str | None

    class Config:
        from_attributes = True


class AssetListResponse(BaseModel):
    """Réponse paginée à GET /assets."""

    items: List[AssetResponse]
    total: int
    skip: int
    limit: int


# Endpoints
@router.get("", response_model=AssetListResponse)
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
    """Liste les actifs de l'inventaire avec filtres optionnels (type, statut, criticité, recherche textuelle)."""
    query = db.query(Asset)

    # Application des filtres de recherche
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
    """Retourne le détail d'un actif par son UUID."""
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


@router.post("", response_model=AssetResponse, status_code=status.HTTP_201_CREATED)
async def create_asset(
    asset_data: AssetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.ASSET_CREATE)),
):
    """Crée un nouvel actif dans l'inventaire."""
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
    """Met à jour partiellement un actif (seuls les champs fournis sont modifiés)."""
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
    """Supprime définitivement un actif et toutes ses vulnérabilités associées (cascade)."""
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found",
        )

    db.delete(asset)
    db.commit()


# ─────────────────────────────────────────────────────────────────────────────
# Agent self-registration
# ─────────────────────────────────────────────────────────────────────────────

class AgentSelfRegister(BaseModel):
    """Corps de la requête POST /register-self envoyée par l'agent Petrix à l'installation."""

    hostname: str
    ips: List[str]
    os: str = "Unknown"
    os_version: str | None = None
    architecture: str | None = None


def _asset_to_response(asset: Asset) -> AssetResponse:
    """Convertit un objet ORM Asset en schéma de réponse AssetResponse."""
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


@router.post("/register-self", response_model=AssetResponse)
async def register_self(
    body: AgentSelfRegister,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Appelé par l'agent Petrix à l'installation — insère ou met à jour la machine dans l'inventaire.

    Effectue un upsert basé sur l'adresse IP principale : si un actif existe déjà avec
    l'une des IP déclarées, il est mis à jour ; sinon un nouvel actif est créé.
    Fonctionne avec tout JWT valide, y compris le token agent longue durée (30 jours).
    """
    now = datetime.utcnow()

    # Recherche d'un actif existant par correspondance sur l'une des IP déclarées
    asset: Optional[Asset] = None
    for ip in body.ips:
        asset = db.query(Asset).filter(Asset.ip_address == ip).first()
        if asset:
            break

    # Déduction du type d'actif à partir du nom de l'OS déclaré par l'agent
    os_lower = body.os.lower()
    if "windows" in os_lower:
        guessed_type = AssetType.WORKSTATION
    elif "darwin" in os_lower or "mac" in os_lower:
        guessed_type = AssetType.WORKSTATION
    else:
        guessed_type = AssetType.SERVER

    if asset:
        # Mise à jour de l'actif existant avec les données courantes de l'agent
        if body.hostname:
            asset.name = body.hostname
            asset.hostname = body.hostname
        if body.os:
            asset.os = body.os
        if body.os_version:
            asset.os_version = body.os_version
        if body.ips:
            asset.ip_address = body.ips[0]
        asset.last_seen = now
        # S'assurer que le tag "agent" est présent pour identifier les actifs auto-enregistrés
        tags = list(asset.tags or [])
        if "agent" not in tags:
            tags.append("agent")
        asset.tags = tags
    else:
        primary_ip = body.ips[0] if body.ips else None
        asset = Asset(
            name=body.hostname or primary_ip or "Unknown",
            hostname=body.hostname,
            ip_address=primary_ip,
            os=body.os,
            os_version=body.os_version,
            asset_type=guessed_type,
            status=AssetStatus.ACTIVE,
            criticality=Severity.MEDIUM,
            tags=["agent"],
            last_seen=now,
        )
        db.add(asset)

    db.commit()
    db.refresh(asset)
    return _asset_to_response(asset)


# ─────────────────────────────────────────────────────────────────────────────
# Statistics
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/stats/summary")
async def get_assets_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.ASSET_VIEW)),
):
    """Retourne un résumé statistique de l'inventaire : total, répartition par type, statut et criticité."""
    total = db.query(Asset).count()

    # Répartition par type d'actif
    by_type = {}
    for asset_type in AssetType:
        count = db.query(Asset).filter(Asset.asset_type == asset_type).count()
        if count > 0:
            by_type[asset_type.value] = count

    # Répartition par statut opérationnel
    by_status = {}
    for status in AssetStatus:
        count = db.query(Asset).filter(Asset.status == status).count()
        if count > 0:
            by_status[status.value] = count

    # Répartition par criticité
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
