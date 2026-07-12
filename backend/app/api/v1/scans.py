"""Endpoints de pilotage des scans réseau : création, démarrage, annulation et consultation des résultats.
Supporte deux modes : scans asynchrones via Celery et scans pilotés par l'agent local — protégé par SCAN_*.
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.permissions import Permission
from app.infrastructure.database import get_db
from app.infrastructure.database.models import Scan, ScanType, ScanStatus, User
from app.api.v1.deps import require_permission

router = APIRouter()


# Schémas Pydantic — requêtes et réponses de l'API de scans

class ScanTarget(BaseModel):
    """Cible d'un scan : IP, nom d'hôte, plage (ex. 192.168.1.0-254) ou sous-réseau CIDR."""

    type: str  # ip, hostname, range, subnet
    value: str


class ScanConfig(BaseModel):
    """Paramètres de configuration du scan : plage de ports, timing Nmap et activation des scripts NSE."""

    model_config = {"extra": "allow"}
    ports: str = "1-1000"
    timing: str = "T3"
    scripts: bool = True
    vuln_scan: bool = True


class ScanCreate(BaseModel):
    """Corps de la requête POST /scans : définition d'un nouveau scan avec ses cibles et sa configuration."""

    name: str
    scan_type: ScanType
    targets: List[ScanTarget]
    config: ScanConfig = ScanConfig()
    scheduled_at: datetime | None = None


class ScanResponse(BaseModel):
    """État complet d'un scan : progression, résultats, score de sécurité et journal des phases."""

    id: str
    name: str
    scan_type: ScanType
    status: ScanStatus
    progress: int
    targets: List[dict]
    config: dict
    score: float | None
    grade: str | None
    risk_level: str | None
    findings_summary: dict
    current_phase: str | None
    phases_completed: List[str]
    scheduled_at: str | None
    started_at: str | None
    completed_at: str | None
    duration_seconds: float | None
    error_message: str | None
    created_by_id: str
    created_at: str

    class Config:
        from_attributes = True


class ScanListResponse(BaseModel):
    """Réponse paginée à GET /scans."""

    items: List[ScanResponse]
    total: int
    skip: int
    limit: int


# Endpoints
@router.get("", response_model=ScanListResponse)
async def list_scans(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    scan_type: Optional[ScanType] = None,
    status: Optional[ScanStatus] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.SCAN_VIEW)),
):
    """Liste les scans avec filtres optionnels (type, statut) — réservé aux rôles possédant SCAN_VIEW."""
    query = db.query(Scan)

    if scan_type:
        query = query.filter(Scan.scan_type == scan_type)
    if status:
        query = query.filter(Scan.status == status)

    total = query.count()
    scans = query.order_by(Scan.created_at.desc()).offset(skip).limit(limit).all()

    return ScanListResponse(
        items=[
            ScanResponse(
                id=str(s.id),
                name=s.name,
                scan_type=s.scan_type,
                status=s.status,
                progress=s.progress,
                targets=s.targets or [],
                config=s.config or {},
                score=s.score,
                grade=s.grade,
                risk_level=s.risk_level,
                findings_summary=s.findings_summary or {},
                current_phase=s.current_phase,
                phases_completed=s.phases_completed or [],
                scheduled_at=s.scheduled_at.isoformat() if s.scheduled_at else None,
                started_at=s.started_at.isoformat() if s.started_at else None,
                completed_at=s.completed_at.isoformat() if s.completed_at else None,
                duration_seconds=s.duration_seconds,
                error_message=s.error_message,
                created_by_id=str(s.created_by_id),
                created_at=s.created_at.isoformat(),
            )
            for s in scans
        ],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/{scan_id}", response_model=ScanResponse)
async def get_scan(
    scan_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.SCAN_VIEW)),
):
    """Retourne l'état détaillé d'un scan par son UUID — réservé SCAN_VIEW."""
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found",
        )

    return ScanResponse(
        id=str(scan.id),
        name=scan.name,
        scan_type=scan.scan_type,
        status=scan.status,
        progress=scan.progress,
        targets=scan.targets or [],
        config=scan.config or {},
        score=scan.score,
        grade=scan.grade,
        risk_level=scan.risk_level,
        findings_summary=scan.findings_summary or {},
        current_phase=scan.current_phase,
        phases_completed=scan.phases_completed or [],
        scheduled_at=scan.scheduled_at.isoformat() if scan.scheduled_at else None,
        started_at=scan.started_at.isoformat() if scan.started_at else None,
        completed_at=scan.completed_at.isoformat() if scan.completed_at else None,
        duration_seconds=scan.duration_seconds,
        error_message=scan.error_message,
        created_by_id=str(scan.created_by_id),
        created_at=scan.created_at.isoformat(),
    )


@router.post("", response_model=ScanResponse, status_code=status.HTTP_201_CREATED)
async def create_scan(
    scan_data: ScanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.SCAN_CREATE)),
):
    """Crée un nouveau scan en statut PENDING ; si config.agent=True, démarre immédiatement en RUNNING — réservé SCAN_CREATE."""
    config_dict = scan_data.config.model_dump()
    is_agent = config_dict.get("agent", False)

    scan = Scan(
        name=scan_data.name,
        scan_type=scan_data.scan_type,
        targets=[t.model_dump() for t in scan_data.targets],
        config=config_dict,
        scheduled_at=scan_data.scheduled_at,
        created_by_id=current_user.id,
    )
    if is_agent:
        scan.status = ScanStatus.RUNNING
        scan.started_at = datetime.utcnow()
        scan.current_phase = "agent_scanning"

    db.add(scan)
    db.commit()
    db.refresh(scan)

    return ScanResponse(
        id=str(scan.id),
        name=scan.name,
        scan_type=scan.scan_type,
        status=scan.status,
        progress=scan.progress,
        targets=scan.targets or [],
        config=scan.config or {},
        score=None,
        grade=None,
        risk_level=None,
        findings_summary=scan.findings_summary or {},
        current_phase=None,
        phases_completed=[],
        scheduled_at=scan.scheduled_at.isoformat() if scan.scheduled_at else None,
        started_at=None,
        completed_at=None,
        duration_seconds=None,
        error_message=None,
        created_by_id=str(scan.created_by_id),
        created_at=scan.created_at.isoformat(),
    )


@router.post("/{scan_id}/start", response_model=ScanResponse)
async def start_scan(
    scan_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.SCAN_EXECUTE)),
):
    """Passe un scan de PENDING à RUNNING et déclenche la tâche Celery d'exécution — réservé SCAN_EXECUTE."""
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found",
        )

    if scan.status != ScanStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot start scan in {scan.status.value} status",
        )

    scan.status = ScanStatus.RUNNING
    scan.started_at = datetime.utcnow()
    scan.current_phase = "initialization"
    db.commit()
    db.refresh(scan)

    from app.workers.scan_tasks import execute_scan
    execute_scan.delay(str(scan.id))

    return ScanResponse(
        id=str(scan.id),
        name=scan.name,
        scan_type=scan.scan_type,
        status=scan.status,
        progress=scan.progress,
        targets=scan.targets or [],
        config=scan.config or {},
        score=scan.score,
        grade=scan.grade,
        risk_level=scan.risk_level,
        findings_summary=scan.findings_summary or {},
        current_phase=scan.current_phase,
        phases_completed=scan.phases_completed or [],
        scheduled_at=scan.scheduled_at.isoformat() if scan.scheduled_at else None,
        started_at=scan.started_at.isoformat() if scan.started_at else None,
        completed_at=None,
        duration_seconds=None,
        error_message=None,
        created_by_id=str(scan.created_by_id),
        created_at=scan.created_at.isoformat(),
    )


@router.post("/{scan_id}/cancel", response_model=ScanResponse)
async def cancel_scan(
    scan_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.SCAN_EXECUTE)),
):
    """Annule un scan PENDING ou RUNNING et enregistre la durée écoulée — réservé SCAN_EXECUTE."""
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found",
        )

    if scan.status not in [ScanStatus.PENDING, ScanStatus.RUNNING]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel scan in {scan.status.value} status",
        )

    scan.status = ScanStatus.CANCELLED
    scan.completed_at = datetime.utcnow()
    if scan.started_at:
        scan.duration_seconds = (scan.completed_at - scan.started_at).total_seconds()
    db.commit()
    db.refresh(scan)

    return ScanResponse(
        id=str(scan.id),
        name=scan.name,
        scan_type=scan.scan_type,
        status=scan.status,
        progress=scan.progress,
        targets=scan.targets or [],
        config=scan.config or {},
        score=scan.score,
        grade=scan.grade,
        risk_level=scan.risk_level,
        findings_summary=scan.findings_summary or {},
        current_phase=scan.current_phase,
        phases_completed=scan.phases_completed or [],
        scheduled_at=scan.scheduled_at.isoformat() if scan.scheduled_at else None,
        started_at=scan.started_at.isoformat() if scan.started_at else None,
        completed_at=scan.completed_at.isoformat() if scan.completed_at else None,
        duration_seconds=scan.duration_seconds,
        error_message=scan.error_message,
        created_by_id=str(scan.created_by_id),
        created_at=scan.created_at.isoformat(),
    )


@router.delete("/{scan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scan(
    scan_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.SCAN_DELETE)),
):
    """Supprime un scan (interdit si le scan est en cours d'exécution) — réservé SCAN_DELETE."""
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found",
        )

    if scan.status == ScanStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete a running scan",
        )

    db.delete(scan)
    db.commit()


@router.get("/{scan_id}/findings")
async def get_scan_findings(
    scan_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.SCAN_VIEW)),
):
    """Retourne les hôtes découverts et les findings détaillés (hôtes/ports) d'un scan terminé — réservé SCAN_VIEW."""
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found")

    raw = scan.config.get("_results") or {}
    return {
        "scan_id": str(scan.id),
        "status": scan.status,
        "hosts": raw.get("hosts", []),
        "findings": raw.get("findings", []),
        "findings_summary": scan.findings_summary or {},
    }


@router.post("/{scan_id}/agent-results", status_code=status.HTTP_200_OK)
async def receive_agent_results(
    scan_id: UUID,
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.SCAN_EXECUTE)),
):
    """Reçoit les résultats poussés par l'agent Petrix local, sauvegarde les findings et crée/met à jour les assets découverts — réservé SCAN_EXECUTE."""
    from app.infrastructure.database.models import Asset, AssetType, AssetStatus, Severity as DbSeverity

    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found")

    hosts = data.get("hosts", [])
    findings = data.get("findings", [])

    # Upsert des assets découverts : création si absent, mise à jour si déjà présent par IP
    assets_created = 0
    for host in hosts:
        ip = host.get("ip")
        if not ip:
            continue
        existing = db.query(Asset).filter(Asset.ip_address == ip).first()
        if not existing:
            asset = Asset(
                name=host.get("hostname") or ip,
                asset_type=AssetType.SERVER,
                status=AssetStatus.ACTIVE,
                criticality=DbSeverity.MEDIUM,
                ip_address=ip,
                mac_address=host.get("mac"),
                hostname=host.get("hostname"),
                os=host.get("os"),
                last_scan_id=scan_id,
            )
            db.add(asset)
            assets_created += 1
        else:
            if host.get("hostname"):
                existing.hostname = host["hostname"]
            if host.get("os"):
                existing.os = host["os"]
            if host.get("mac"):
                existing.mac_address = host["mac"]
            existing.last_scan_id = scan_id

    updated_config = dict(scan.config or {})
    updated_config["_results"] = {"hosts": hosts, "findings": findings}
    scan.config = updated_config
    scan.status = ScanStatus.RUNNING
    db.commit()
    return {"ok": True, "assets_created": assets_created}


@router.get("/{scan_id}/assets", status_code=status.HTTP_200_OK)
async def get_scan_assets(
    scan_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.SCAN_VIEW)),
):
    """Retourne les assets découverts ou mis à jour lors d'un scan spécifique — réservé SCAN_VIEW."""
    from app.infrastructure.database.models import Asset as AssetModel
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found")

    assets = db.query(AssetModel).filter(AssetModel.last_scan_id == scan_id).all()
    return [
        {
            "id": str(a.id),
            "name": a.name,
            "ip_address": a.ip_address,
            "hostname": a.hostname,
            "os": a.os,
            "asset_type": a.asset_type,
            "status": a.status,
            "last_seen": a.last_seen.isoformat() if a.last_seen else None,
        }
        for a in assets
    ]


@router.patch("/{scan_id}/agent-complete", status_code=status.HTTP_200_OK)
async def agent_complete(
    scan_id: UUID,
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.SCAN_EXECUTE)),
):
    """Marque un scan agent comme terminé, calcule la durée et le niveau de risque — réservé SCAN_EXECUTE."""
    from datetime import datetime
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found")

    summary = data.get("summary", {})
    score = float(data.get("score", 100))
    grade = data.get("grade", "A")
    risk = "low" if score >= 75 else "medium" if score >= 50 else "high"

    scan.status = ScanStatus.COMPLETED
    scan.findings_summary = summary
    scan.score = score
    scan.grade = grade
    scan.risk_level = risk
    scan.completed_at = datetime.utcnow()
    if scan.started_at:
        scan.duration_seconds = (scan.completed_at - scan.started_at).total_seconds()
    db.commit()
    return {"ok": True}


# Statistics
@router.get("/stats/summary")
async def get_scans_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.SCAN_VIEW)),
):
    """Retourne les statistiques des scans : répartition par statut, type et 5 derniers scans complétés — réservé SCAN_VIEW."""
    total = db.query(Scan).count()

    # Répartition par statut
    by_status = {}
    for status in ScanStatus:
        count = db.query(Scan).filter(Scan.status == status).count()
        if count > 0:
            by_status[status.value] = count

    # Répartition par type de scan
    by_type = {}
    for scan_type in ScanType:
        count = db.query(Scan).filter(Scan.scan_type == scan_type).count()
        if count > 0:
            by_type[scan_type.value] = count

    # Derniers scans terminés
    recent_completed = (
        db.query(Scan)
        .filter(Scan.status == ScanStatus.COMPLETED)
        .order_by(Scan.completed_at.desc())
        .limit(5)
        .all()
    )

    return {
        "total": total,
        "by_status": by_status,
        "by_type": by_type,
        "recent_completed": [
            {
                "id": str(s.id),
                "name": s.name,
                "grade": s.grade,
                "score": s.score,
                "completed_at": s.completed_at.isoformat() if s.completed_at else None,
            }
            for s in recent_completed
        ],
    }
