"""Vulnerabilities management endpoints."""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.permissions import Permission
from app.infrastructure.database import get_db
from app.infrastructure.database.models import (
    Vulnerability,
    Severity,
    VulnStatus,
    User,
)
from app.api.v1.deps import get_current_active_user, require_permission

router = APIRouter()


# Schemas
class VulnBase(BaseModel):
    title: str
    description: str | None = None
    category: str = "general"
    severity: Severity
    cvss_score: float | None = None
    cvss_vector: str | None = None
    cve_ids: List[str] = []
    cwe_ids: List[str] = []
    affected_component: str | None = None
    port: int | None = None
    service: str | None = None
    protocol: str | None = None
    evidence: str | None = None
    remediation: str | None = None
    remediation_effort: str | None = None
    references: List[str] = []


class VulnCreate(VulnBase):
    asset_id: UUID | None = None


class VulnUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    category: str | None = None
    severity: Severity | None = None
    status: VulnStatus | None = None
    cvss_score: float | None = None
    remediation: str | None = None
    assignee_id: UUID | None = None
    due_date: datetime | None = None


class VulnResponse(VulnBase):
    id: str
    asset_id: str | None
    scan_id: str | None
    status: VulnStatus
    assignee_id: str | None
    due_date: str | None
    ai_priority_score: float | None
    ai_remediation: str | None
    discovered_at: str
    discovered_by: str
    resolved_at: str | None
    created_at: str

    class Config:
        from_attributes = True


class VulnListResponse(BaseModel):
    items: List[VulnResponse]
    total: int
    skip: int
    limit: int


# Endpoints
@router.get("/", response_model=VulnListResponse)
async def list_vulnerabilities(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    severity: Optional[Severity] = None,
    status: Optional[VulnStatus] = None,
    asset_id: Optional[UUID] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.VULN_VIEW)),
):
    """List vulnerabilities with optional filters."""
    query = db.query(Vulnerability)

    # Apply filters
    if severity:
        query = query.filter(Vulnerability.severity == severity)
    if status:
        query = query.filter(Vulnerability.status == status)
    if asset_id:
        query = query.filter(Vulnerability.asset_id == asset_id)
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (Vulnerability.title.ilike(search_filter))
            | (Vulnerability.description.ilike(search_filter))
        )

    total = query.count()
    vulns = query.order_by(Vulnerability.discovered_at.desc()).offset(skip).limit(limit).all()

    return VulnListResponse(
        items=[
            VulnResponse(
                id=str(v.id),
                title=v.title,
                description=v.description,
                category=v.category,
                severity=v.severity,
                status=v.status,
                cvss_score=v.cvss_score,
                cvss_vector=v.cvss_vector,
                cve_ids=v.cve_ids or [],
                cwe_ids=v.cwe_ids or [],
                affected_component=v.affected_component,
                port=v.port,
                service=v.service,
                protocol=v.protocol,
                evidence=v.evidence,
                remediation=v.remediation,
                remediation_effort=v.remediation_effort,
                references=v.references or [],
                asset_id=str(v.asset_id) if v.asset_id else None,
                scan_id=str(v.scan_id) if v.scan_id else None,
                assignee_id=str(v.assignee_id) if v.assignee_id else None,
                due_date=v.due_date.isoformat() if v.due_date else None,
                ai_priority_score=v.ai_priority_score,
                ai_remediation=v.ai_remediation,
                discovered_at=v.discovered_at.isoformat(),
                discovered_by=v.discovered_by,
                resolved_at=v.resolved_at.isoformat() if v.resolved_at else None,
                created_at=v.created_at.isoformat(),
            )
            for v in vulns
        ],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/{vuln_id}", response_model=VulnResponse)
async def get_vulnerability(
    vuln_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.VULN_VIEW)),
):
    """Get a specific vulnerability."""
    vuln = db.query(Vulnerability).filter(Vulnerability.id == vuln_id).first()
    if not vuln:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vulnerability not found",
        )

    return VulnResponse(
        id=str(vuln.id),
        title=vuln.title,
        description=vuln.description,
        category=vuln.category,
        severity=vuln.severity,
        status=vuln.status,
        cvss_score=vuln.cvss_score,
        cvss_vector=vuln.cvss_vector,
        cve_ids=vuln.cve_ids or [],
        cwe_ids=vuln.cwe_ids or [],
        affected_component=vuln.affected_component,
        port=vuln.port,
        service=vuln.service,
        protocol=vuln.protocol,
        evidence=vuln.evidence,
        remediation=vuln.remediation,
        remediation_effort=vuln.remediation_effort,
        references=vuln.references or [],
        asset_id=str(vuln.asset_id) if vuln.asset_id else None,
        scan_id=str(vuln.scan_id) if vuln.scan_id else None,
        assignee_id=str(vuln.assignee_id) if vuln.assignee_id else None,
        due_date=vuln.due_date.isoformat() if vuln.due_date else None,
        ai_priority_score=vuln.ai_priority_score,
        ai_remediation=vuln.ai_remediation,
        discovered_at=vuln.discovered_at.isoformat(),
        discovered_by=vuln.discovered_by,
        resolved_at=vuln.resolved_at.isoformat() if vuln.resolved_at else None,
        created_at=vuln.created_at.isoformat(),
    )


@router.post("/", response_model=VulnResponse, status_code=status.HTTP_201_CREATED)
async def create_vulnerability(
    vuln_data: VulnCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.VULN_CREATE)),
):
    """Create a new vulnerability."""
    vuln = Vulnerability(
        title=vuln_data.title,
        description=vuln_data.description,
        category=vuln_data.category,
        severity=vuln_data.severity,
        cvss_score=vuln_data.cvss_score,
        cvss_vector=vuln_data.cvss_vector,
        cve_ids=vuln_data.cve_ids,
        cwe_ids=vuln_data.cwe_ids,
        affected_component=vuln_data.affected_component,
        port=vuln_data.port,
        service=vuln_data.service,
        protocol=vuln_data.protocol,
        evidence=vuln_data.evidence,
        remediation=vuln_data.remediation,
        remediation_effort=vuln_data.remediation_effort,
        references=vuln_data.references,
        asset_id=vuln_data.asset_id,
        discovered_by="manual",
    )
    db.add(vuln)
    db.commit()
    db.refresh(vuln)

    return VulnResponse(
        id=str(vuln.id),
        title=vuln.title,
        description=vuln.description,
        category=vuln.category,
        severity=vuln.severity,
        status=vuln.status,
        cvss_score=vuln.cvss_score,
        cvss_vector=vuln.cvss_vector,
        cve_ids=vuln.cve_ids or [],
        cwe_ids=vuln.cwe_ids or [],
        affected_component=vuln.affected_component,
        port=vuln.port,
        service=vuln.service,
        protocol=vuln.protocol,
        evidence=vuln.evidence,
        remediation=vuln.remediation,
        remediation_effort=vuln.remediation_effort,
        references=vuln.references or [],
        asset_id=str(vuln.asset_id) if vuln.asset_id else None,
        scan_id=None,
        assignee_id=None,
        due_date=None,
        ai_priority_score=None,
        ai_remediation=None,
        discovered_at=vuln.discovered_at.isoformat(),
        discovered_by=vuln.discovered_by,
        resolved_at=None,
        created_at=vuln.created_at.isoformat(),
    )


@router.patch("/{vuln_id}", response_model=VulnResponse)
async def update_vulnerability(
    vuln_id: UUID,
    vuln_data: VulnUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.VULN_EDIT)),
):
    """Update a vulnerability."""
    vuln = db.query(Vulnerability).filter(Vulnerability.id == vuln_id).first()
    if not vuln:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vulnerability not found",
        )

    update_data = vuln_data.model_dump(exclude_unset=True)

    # Handle status change to resolved
    if "status" in update_data and update_data["status"] == VulnStatus.RESOLVED:
        update_data["resolved_at"] = datetime.utcnow()

    for field, value in update_data.items():
        setattr(vuln, field, value)

    db.commit()
    db.refresh(vuln)

    return VulnResponse(
        id=str(vuln.id),
        title=vuln.title,
        description=vuln.description,
        category=vuln.category,
        severity=vuln.severity,
        status=vuln.status,
        cvss_score=vuln.cvss_score,
        cvss_vector=vuln.cvss_vector,
        cve_ids=vuln.cve_ids or [],
        cwe_ids=vuln.cwe_ids or [],
        affected_component=vuln.affected_component,
        port=vuln.port,
        service=vuln.service,
        protocol=vuln.protocol,
        evidence=vuln.evidence,
        remediation=vuln.remediation,
        remediation_effort=vuln.remediation_effort,
        references=vuln.references or [],
        asset_id=str(vuln.asset_id) if vuln.asset_id else None,
        scan_id=str(vuln.scan_id) if vuln.scan_id else None,
        assignee_id=str(vuln.assignee_id) if vuln.assignee_id else None,
        due_date=vuln.due_date.isoformat() if vuln.due_date else None,
        ai_priority_score=vuln.ai_priority_score,
        ai_remediation=vuln.ai_remediation,
        discovered_at=vuln.discovered_at.isoformat(),
        discovered_by=vuln.discovered_by,
        resolved_at=vuln.resolved_at.isoformat() if vuln.resolved_at else None,
        created_at=vuln.created_at.isoformat(),
    )


@router.delete("/{vuln_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vulnerability(
    vuln_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.VULN_DELETE)),
):
    """Delete a vulnerability."""
    vuln = db.query(Vulnerability).filter(Vulnerability.id == vuln_id).first()
    if not vuln:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vulnerability not found",
        )

    db.delete(vuln)
    db.commit()


# Statistics
@router.get("/stats/summary")
async def get_vulns_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.VULN_VIEW)),
):
    """Get vulnerabilities statistics."""
    total = db.query(Vulnerability).count()
    open_count = db.query(Vulnerability).filter(Vulnerability.status == VulnStatus.OPEN).count()

    # By severity
    by_severity = {}
    for severity in Severity:
        count = db.query(Vulnerability).filter(Vulnerability.severity == severity).count()
        if count > 0:
            by_severity[severity.value] = count

    # By status
    by_status = {}
    for status in VulnStatus:
        count = db.query(Vulnerability).filter(Vulnerability.status == status).count()
        if count > 0:
            by_status[status.value] = count

    return {
        "total": total,
        "open": open_count,
        "by_severity": by_severity,
        "by_status": by_status,
    }
