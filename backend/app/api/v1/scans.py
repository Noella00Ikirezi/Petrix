"""Scans management endpoints."""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.permissions import Permission
from app.infrastructure.database import get_db
from app.infrastructure.database.models import Scan, ScanType, ScanStatus, User
from app.api.v1.deps import get_current_active_user, require_permission

router = APIRouter()


# Schemas
class ScanTarget(BaseModel):
    type: str  # ip, hostname, range, subnet
    value: str


class ScanConfig(BaseModel):
    ports: str = "1-1000"
    timing: str = "T3"
    scripts: bool = True
    vuln_scan: bool = True


class ScanCreate(BaseModel):
    name: str
    scan_type: ScanType
    targets: List[ScanTarget]
    config: ScanConfig = ScanConfig()
    scheduled_at: datetime | None = None


class ScanResponse(BaseModel):
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
    items: List[ScanResponse]
    total: int
    skip: int
    limit: int


# Endpoints
@router.get("/", response_model=ScanListResponse)
async def list_scans(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    scan_type: Optional[ScanType] = None,
    status: Optional[ScanStatus] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.SCAN_VIEW)),
):
    """List scans with optional filters."""
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
    """Get a specific scan."""
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


@router.post("/", response_model=ScanResponse, status_code=status.HTTP_201_CREATED)
async def create_scan(
    scan_data: ScanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.SCAN_CREATE)),
):
    """Create a new scan."""
    scan = Scan(
        name=scan_data.name,
        scan_type=scan_data.scan_type,
        targets=[t.model_dump() for t in scan_data.targets],
        config=scan_data.config.model_dump(),
        scheduled_at=scan_data.scheduled_at,
        created_by_id=current_user.id,
    )
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
    """Start a pending scan."""
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

    # Update status to running
    scan.status = ScanStatus.RUNNING
    scan.started_at = datetime.utcnow()
    scan.current_phase = "initialization"
    db.commit()
    db.refresh(scan)

    # TODO: Trigger Celery task for actual scanning
    # from app.workers.scan_tasks import execute_scan
    # execute_scan.delay(str(scan.id))

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
    """Cancel a running scan."""
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
    """Delete a scan."""
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


# Statistics
@router.get("/stats/summary")
async def get_scans_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.SCAN_VIEW)),
):
    """Get scans statistics."""
    total = db.query(Scan).count()

    # By status
    by_status = {}
    for status in ScanStatus:
        count = db.query(Scan).filter(Scan.status == status).count()
        if count > 0:
            by_status[status.value] = count

    # By type
    by_type = {}
    for scan_type in ScanType:
        count = db.query(Scan).filter(Scan.scan_type == scan_type).count()
        if count > 0:
            by_type[scan_type.value] = count

    # Recent completed
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
